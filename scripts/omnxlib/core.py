"""Small, defensive I/O and schema layer. All mutations are explicit.

Locks coordinate cooperating local processes, not distributed hosts. POSIX
openat/O_NOFOLLOW pins directory descriptors; Windows uses a checked fallback.
"""
from __future__ import annotations
import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import unicodedata
import uuid

VENDOR = Path(__file__).resolve().parents[1] / '_vendor'
sys.path.insert(0, str(VENDOR))
import yaml

MAX_DOCUMENT = 8 * 1024 * 1024
PACKAGE = Path(__file__).resolve().parents[2]

class MethodError(Exception):
    def __init__(self, code: str, summary: str, exit_code: int = 2, **details):
        super().__init__(summary)
        self.code, self.summary, self.exit_code, self.details = code, summary, exit_code, details

def require(condition, code, summary, exit_code=2, **details):
    if not condition:
        raise MethodError(code, summary, exit_code, **details)

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')

def timestamp(value):
    require(isinstance(value, str), 'invalid_time', 'Timestamp deve ser texto com fuso.')
    try:
        out = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise MethodError('invalid_time', 'Timestamp inválido.') from None
    require(out.tzinfo is not None, 'invalid_time', 'Timestamp sem fuso não é aceito.')
    return out

def new_id(prefix):
    return f'{prefix}-{uuid.uuid4()}'

def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def object_digest(obj):
    return digest(canonical(obj))

def json_bytes(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')

def _pairs(pairs):
    out = {}
    for key, val in pairs:
        require(key not in out, 'duplicate_key', 'Chave duplicada em documento JSON.')
        out[key] = val
    return out

def _depth_check(obj, depth=0, budget=None):
    if budget is None: budget = [100000]
    budget[0] -= 1
    require(depth <= 48 and budget[0] >= 0, 'document_limit', 'Documento excede limites estruturais.')
    if isinstance(obj, dict):
        for k,v in obj.items():
            require(isinstance(k,str), 'invalid_key', 'Chaves devem ser strings.')
            _depth_check(v,depth+1,budget)
    elif isinstance(obj,list):
        for v in obj: _depth_check(v,depth+1,budget)
    else:
        require(obj is None or type(obj) in (str, int, float, bool), 'invalid_scalar', 'Tipo não suportado no documento.')
        if type(obj) is float:
            import math
            require(math.isfinite(obj),'invalid_number','Número não finito não é aceito.')

class StrictLoader(yaml.SafeLoader):
    """Safe YAML without aliases, non-string keys, implicit timestamps or merges."""
    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent):
            raise MethodError('yaml_alias', 'Aliases YAML não são suportados; use valores explícitos.')
        depth = getattr(self, '_method_depth', 0)
        require(depth < 48, 'document_limit', 'YAML excede profundidade permitida.')
        self._method_depth = depth + 1
        try: return super().compose_node(parent,index)
        finally: self._method_depth = depth
    def construct_mapping(self,node,deep=False):
        out={}
        for key_node,val_node in node.value:
            key=self.construct_object(key_node,deep=deep)
            require(isinstance(key,str),'invalid_key','Chave YAML não textual ou merge não permitido.')
            require(key not in out,'duplicate_key','Chave duplicada em YAML.')
            out[key]=self.construct_object(val_node,deep=deep)
        return out

StrictLoader.yaml_implicit_resolvers = {k:[(tag,rx) for tag,rx in v if tag != 'tag:yaml.org,2002:timestamp'] for k,v in yaml.SafeLoader.yaml_implicit_resolvers.items()}

def load_data(raw: bytes | str, *, yaml_ok=False):
    if isinstance(raw,str): raw=raw.encode('utf-8')
    require(len(raw)<=MAX_DOCUMENT,'document_limit','Documento excede 8 MiB.')
    try:
        text=raw.decode('utf-8-sig')
        if yaml_ok:
            obj=yaml.load(text,Loader=StrictLoader)
        else:
            obj=json.loads(text, object_pairs_hook=_pairs, parse_constant=lambda _: (_ for _ in ()).throw(MethodError('invalid_number','Número JSON inválido.')))
        _depth_check(obj)
        return obj
    except MethodError: raise
    except (ValueError,UnicodeError,yaml.YAMLError,RecursionError):
        # Parser messages can contain secrets from source lines. Do not echo them.
        raise MethodError('invalid_document','Documento não pôde ser lido como JSON/YAML seguro.') from None

def portable_path(value: str):
    require(isinstance(value,str) and 0<len(value)<=1024,'invalid_path','Path relativo inválido.')
    require('\\' not in value and not value.startswith('/') and '\x00' not in value,'invalid_path','Path deve ser relativo, POSIX e sem travessia.')
    parts=value.split('/')
    bad={'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}
    for part in parts:
        require(part not in ('','.','..') and not part.endswith((' ','.')),'invalid_path','Componente de path inválido.')
        require(not any(ord(c)<32 for c in part) and not any(c in part for c in ':<>"|?*'),'invalid_path','Path não portátil.')
        require(part.split('.')[0].upper() not in bad,'invalid_path','Nome reservado de dispositivo.')
        require(unicodedata.normalize('NFC',part)==part,'invalid_path','Normalize o path Unicode para NFC.')
    return value

class RootFS:
    def __init__(self,root):
        raw=Path(root).absolute()
        # Reject symlinks in the explicit root, not just in descendants.
        for p in (raw,*raw.parents):
            require(not p.is_symlink(),'unsafe_root','A raiz não pode atravessar symlink.')
        self.root=raw.resolve()
        require(self.root.is_dir(),'missing_root','Raiz não é um diretório existente.')
        self.posix=(os.name=='posix' and hasattr(os,'O_NOFOLLOW'))

    def path(self,rel):
        portable_path(rel)
        p=self.root
        for i,part in enumerate(rel.split('/')):
            p=p/part
            if p.is_symlink(): raise MethodError('unsafe_link','Symlink não é permitido nesta operação.')
            if p.exists():
                st=p.stat()
                if stat.S_ISREG(st.st_mode): require(st.st_nlink==1,'unsafe_link','Hardlink não é permitido nesta operação.')
                elif not stat.S_ISDIR(st.st_mode): raise MethodError('unsafe_file','Arquivo especial não é permitido.')
                if i<len(rel.split('/'))-1:
                    require(p.is_dir(),'path_conflict','Um componente de diretório está ocupado por arquivo.',3)
        return p

    @contextlib.contextmanager
    def parent(self,rel,create=False):
        portable_path(rel)
        self.path(rel)
        parts=rel.split('/')
        if not self.posix:
            p=self.path(rel)
            if create: p.parent.mkdir(parents=True,exist_ok=True)
            yield None,p.name,p.parent
            return
        fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:
            for part in parts[:-1]:
                try: nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
                except FileNotFoundError:
                    if not create: raise
                    os.mkdir(part,mode=0o700,dir_fd=fd)
                    nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
                os.close(fd); fd=nxt
            yield fd,parts[-1],None
        except OSError as e:
            if e.errno in (40,20): raise MethodError('unsafe_path','Path substituído ou não seguro.',3) from None
            raise
        finally: os.close(fd)

    def read(self,rel,limit=MAX_DOCUMENT):
        try:
            with self.parent(rel) as (fd,name,parent):
                flags=os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)
                f=os.open(name if fd is not None else parent/name,flags,dir_fd=fd)
                with os.fdopen(f,'rb') as h:
                    st=os.fstat(h.fileno())
                    require(stat.S_ISREG(st.st_mode) and st.st_nlink==1,'unsafe_file','Somente arquivo regular sem hardlinks.')
                    require(st.st_size<=limit,'document_limit','Arquivo excede limite de leitura.')
                    raw=h.read(limit+1)
                    require(len(raw)<=limit,'document_limit','Arquivo cresceu além do limite de leitura.')
                    return raw
        except FileNotFoundError: return None

    def hash(self,rel):
        b=self.read(rel)
        return None if b is None else digest(b)

    def write(self,rel,raw:bytes,expected,mode=0o600):
        require(isinstance(raw,bytes),'internal_type','Escrita exige bytes.')
        require(self.hash(rel)==expected,'stale_state','Conteúdo mudou; releia antes de gravar.',3,path=rel)
        with self.parent(rel,create=True) as (fd,name,parent):
            tmp=f'.omnx-tmp-{uuid.uuid4().hex}'
            p=tmp if fd is not None else parent/tmp
            hfd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),mode,dir_fd=fd)
            try:
                with os.fdopen(hfd,'wb') as h:
                    h.write(raw); h.flush(); os.fsync(h.fileno())
                require(self.hash(rel)==expected,'stale_state','Conteúdo mudou durante preparação da escrita.',3,path=rel)
                if fd is not None:
                    os.replace(tmp,name,src_dir_fd=fd,dst_dir_fd=fd); os.fsync(fd)
                else: os.replace(parent/tmp,parent/name)
            finally:
                try:
                    if fd is not None: os.unlink(tmp,dir_fd=fd)
                    else: (parent/tmp).unlink()
                except FileNotFoundError: pass

    def delete(self,rel,expected):
        require(expected is not None and self.hash(rel)==expected,'stale_state','Arquivo removido ou alterado; remoção cancelada.',3,path=rel)
        with self.parent(rel) as (fd,name,parent):
            if fd is not None: os.unlink(name,dir_fd=fd); os.fsync(fd)
            else: (parent/name).unlink()

    def data(self,rel,*,yaml_ok=False):
        raw=self.read(rel)
        return None if raw is None else load_data(raw,yaml_ok=yaml_ok)

    def local(self):
        # Do not make historical instruction files discoverable; backups use .bin.
        rel='.omnx/local/.gitignore'
        if self.read(rel) is None:
            self.write(rel,b'*\n',None)
        p=self.path('.omnx/local')
        if os.name=='posix': os.chmod(p,0o700)
        return p

@contextlib.contextmanager
def metadata_lock(fs:RootFS, resource='metadata'):
    require(re.fullmatch(r'[a-z0-9-]{1,48}',resource) is not None,'invalid_lock','Nome de lock inválido.')
    fs.local()
    rel=f'.omnx/local/locks/{resource}.lock'
    with fs.parent(rel,True) as (dirfd,name,parent):
        fd=os.open(name if dirfd is not None else parent/name,os.O_RDWR|os.O_CREAT|getattr(os,'O_NOFOLLOW',0),0o600,dir_fd=dirfd)
    try:
        require(os.fstat(fd).st_nlink==1,'unsafe_link','Lock com hardlink recusado.')
        if os.name=='posix':
            import fcntl
            try: fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError: raise MethodError('locked','Outro processo está escrevendo estes metadados.',3) from None
        else:
            import msvcrt
            try: msvcrt.locking(fd,msvcrt.LK_NBLCK,1)
            except OSError: raise MethodError('locked','Metadados ocupados por outra execução.',3) from None
        owner=json_bytes({'token':uuid.uuid4().hex,'pid':os.getpid(),'created_at':now(),'resource':resource})
        os.lseek(fd,0,0); os.ftruncate(fd,0); os.write(fd,owner); os.fsync(fd)
        yield
    finally:
        os.close(fd) # OS releases the lock on close/crash. Never unlink its inode.

# This validator deliberately implements only the documented, tested subset
# used by the bundled schemas; unsupported schema keywords fail closed.
KEYWORDS={'$schema','$id','title','description','type','properties','required','additionalProperties','items','enum','const','pattern','minLength','maxLength','minimum','maximum','minItems','maxItems','uniqueItems','anyOf'}

def validate(value,schema,path='$'):
    require(isinstance(schema,dict) and not(set(schema)-KEYWORDS),'unsupported_schema','Schema usa keyword não suportada pelo runtime.')
    if 'anyOf' in schema:
        for option in schema['anyOf']:
            try: validate(value,option,path); break
            except MethodError: pass
        else: raise MethodError('schema_validation',f'{path}: nenhum tipo permitido corresponde.')
    typ=schema.get('type')
    def istype(t):
        return {'object':type(value)is dict,'array':type(value)is list,'string':type(value)is str,'integer':type(value)is int,'number':type(value)in(int,float),'boolean':type(value)is bool,'null':value is None}.get(t,False)
    if typ is not None: require(any(istype(t) for t in (typ if isinstance(typ,list) else [typ])),'schema_validation',f'{path}: tipo incorreto.')
    if 'const' in schema: require(value==schema['const'] and type(value)is type(schema['const']),'schema_validation',f'{path}: valor constante incorreto.')
    if 'enum' in schema: require(any(value==v and type(value)is type(v) for v in schema['enum']),'schema_validation',f'{path}: enum não suportado.')
    if isinstance(value,dict):
        require(all(k in value for k in schema.get('required',[])),'schema_validation',f'{path}: campo obrigatório ausente.')
        props=schema.get('properties',{})
        extra=set(value)-set(props)
        if schema.get('additionalProperties') is False: require(not extra,'schema_validation',f'{path}: campo desconhecido; não será descartado.')
        for key,val in value.items():
            if key in props: validate(val,props[key],path+'.'+key)
            elif isinstance(schema.get('additionalProperties'),dict): validate(val,schema['additionalProperties'],path+'.*')
    if isinstance(value,list):
        require(len(value)>=schema.get('minItems',0) and len(value)<=schema.get('maxItems',100000),'schema_validation',f'{path}: tamanho de array inválido.')
        if schema.get('uniqueItems'): require(len({canonical(v) for v in value})==len(value),'schema_validation',f'{path}: itens duplicados.')
        for i,val in enumerate(value):
            if 'items' in schema: validate(val,schema['items'],f'{path}[{i}]')
    if isinstance(value,str):
        require(schema.get('minLength',0)<=len(value)<=schema.get('maxLength',MAX_DOCUMENT),'schema_validation',f'{path}: comprimento inválido.')
        if 'pattern' in schema: require(re.search(schema['pattern'],value) is not None,'schema_validation',f'{path}: formato inválido.')
    if type(value) in (int,float):
        require(value>=schema.get('minimum',float('-inf')) and value<=schema.get('maximum',float('inf')),'schema_validation',f'{path}: número fora dos limites.')
    return value

def schema(name,area='schemas'):
    return load_data((PACKAGE/area/(name+'.schema.json')).read_bytes())

def result(summary,*,changed_paths=None,limitations=None,**data):
    return {'status':'ok','code':'OK','summary':summary,'changed_paths':changed_paths or [],'limitations':limitations or [],**data}

def external_data(path,*,yaml_ok=False):
    p=Path(path).absolute(); fs=RootFS(p.parent)
    data=fs.data(p.name,yaml_ok=yaml_ok)
    require(data is not None,'missing_file','Arquivo externo necessário não existe.',4)
    return data

def emit(obj,output=None):
    data=json_bytes(obj)
    if output:
        p=Path(output).absolute()
        fs=RootFS(p.parent)
        current=fs.read(p.name)
        require(current is None or current==data,'output_exists','Saída já existe com outro conteúdo; escolha outro caminho.',3)
        if current is None: fs.write(p.name,data,None)
        print(json.dumps({'status':'ok','code':'OUTPUT_WRITTEN','summary':'Saída gravada explicitamente.','changed_paths':[str(p)],'limitations':[]},ensure_ascii=False))
    else:
        print(data.decode('utf-8'),end='')
