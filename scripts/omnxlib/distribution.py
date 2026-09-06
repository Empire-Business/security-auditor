"""Offline, digest-pinned extraction into a NEW versioned directory.

Never executes downloaded code, never erases/overwrites an existing installation.
Switching the host's active skill directory is an explicit host operation.
"""
from __future__ import annotations
import io
import zipfile
from .core import *

def semver(s):
    m=re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-([0-9A-Za-z.-]+))?',s)
    require(m is not None,'invalid_version','Versão deve seguir SemVer suportado.')
    base=tuple(map(int,m.groups()[:3]));pre=m[4]
    if pre:
        require(all(part and (not part.isdigit() or part=='0' or not part.startswith('0')) for part in pre.split('.')),'invalid_version','Pré-release SemVer inválida.')
    return base,pre

def compare_versions(a,b):
    x,xp=semver(a);y,yp=semver(b)
    if x!=y:return (x>y)-(x<y)
    if xp==yp:return 0
    if xp is None:return 1
    if yp is None:return -1
    aa=xp.split('.');bb=yp.split('.')
    for i,j in zip(aa,bb):
        if i==j:continue
        if i.isdigit() and j.isdigit():return (int(i)>int(j))-(int(i)<int(j))
        if i.isdigit()!=j.isdigit():return -1 if i.isdigit() else 1
        return (i>j)-(i<j)
    return (len(aa)>len(bb))-(len(aa)<len(bb))

def inspect_archive(archive,expected_digest):
    require(re.fullmatch('[a-f0-9]{64}',expected_digest or '') is not None,'trusted_digest_required','Informe SHA-256 esperado obtido de origem explicitamente confiada.')
    p=Path(archive).absolute();raw=RootFS(p.parent).read(p.name,64*1024*1024)
    require(raw is not None and digest(raw)==expected_digest,'artifact_integrity','Arquivo difere do digest esperado.',5)
    try:z=zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile:raise MethodError('invalid_zip','ZIP inválido.') from None
    files={};case=set();total=0;roots=set()
    with z:
        require(len(z.infolist())<=3000,'archive_limit','ZIP tem entradas demais.')
        for info in z.infolist():
            name=info.filename.rstrip('/');portable_path(name)
            require(not(info.flag_bits&1),'encrypted_archive','ZIP criptografado não é suportado.')
            unix=(info.external_attr>>16)&0xffff
            require(stat.S_IFMT(unix) in (0,stat.S_IFREG,stat.S_IFDIR),'archive_link','ZIP contém links ou arquivos especiais.',5)
            require(name.casefold() not in case,'archive_collision','ZIP contém path duplicado ou colisão de caixa.',5);case.add(name.casefold())
            roots.add(name.split('/')[0])
            if info.is_dir():continue
            total+=info.file_size
            require(info.file_size<=MAX_DOCUMENT and total<=48*1024*1024,'archive_limit','ZIP excede limites de expansão.',5)
            require(info.file_size<=max(1024*1024,info.compress_size*250),'archive_ratio','Razão de expansão excessiva.',5)
            content=z.read(info);require(len(content)==info.file_size,'archive_integrity','Tamanho extraído diverge.',5);files[name]=content
    require(len(roots)==1 and next(iter(roots)) in ('omnx-code','security-auditor'),'archive_root','ZIP deve conter uma raiz de skill reconhecida.')
    root=next(iter(roots));prefix=root+'/'
    require(all(k.startswith(prefix) for k in files),'archive_path_conflict','Arquivo ocupa a raiz do pacote.',5)
    for name in files:
        parts=name.split('/')
        require(not any('/'.join(parts[:i]) in files for i in range(1,len(parts))),'archive_path_conflict','Arquivo e diretório ocupam o mesmo path no ZIP.',5)
    files={k[len(prefix):]:v for k,v in files.items()}
    require('manifest.json' in files and 'SKILL.md' in files and 'integrity.json' in files,'incomplete_package','Pacote precisa de manifest, SKILL e inventário de integridade.')
    m=load_data(files['manifest.json']);require(m['name']==root and m['audit_contract_versions']==['2.0'],'incompatible_package','Nome/contrato do pacote incompatível.',4);semver(m['version'])
    idx=load_data(files['integrity.json'])
    require(idx.get('algorithm')=='sha256' and isinstance(idx.get('files'),dict),'invalid_inventory','Inventário de integridade inválido.')
    actual={k:digest(v) for k,v in files.items() if k!='integrity.json'}
    require(idx['files']==actual,'package_integrity','Inventário do pacote não corresponde aos bytes.',5)
    return files,m

def plan(archive,expected_digest,destination,current_version=None):
    files,m=inspect_archive(archive,expected_digest)
    dest=Path(destination).absolute();RootFS(dest.parent).path(dest.name)
    require(not dest.exists(),'occupied_installation','Destino deve ser novo. Preserve a versão anterior; escolha diretório versionado.',3)
    if current_version:require(compare_versions(m['version'],current_version)>=0,'downgrade_blocked','Downgrade não é aplicado por este instalador.',5)
    data={'schema_version':1,'operation':'install_versioned','archive':str(Path(archive).absolute()),'expected_sha256':expected_digest,'destination':str(dest),'name':m['name'],'version':m['version'],'current_version':current_version,'file_count':len(files)}
    data['plan_digest']=object_digest(data);return data

def apply(p,approved_digest):
    require(set(p)=={'schema_version','operation','archive','expected_sha256','destination','name','version','current_version','file_count','plan_digest'},'invalid_install_plan','Campos do plano de instalação inválidos.')
    require(p['plan_digest']==object_digest({k:v for k,v in p.items() if k!='plan_digest'})==approved_digest,'unapproved_plan','Digest de plano divergente.',5)
    require(p['schema_version']==1 and p['operation']=='install_versioned','invalid_install_plan','Operação de instalação desconhecida.')
    files,m=inspect_archive(p['archive'],p['expected_sha256'])
    require(m['name']==p['name'] and m['version']==p['version'] and len(files)==p['file_count'],'stale_install_plan','Pacote não corresponde ao plano.',3)
    if p['current_version']:require(compare_versions(m['version'],p['current_version'])>=0,'downgrade_blocked','Downgrade não permitido.',5)
    dest=Path(p['destination']);parent=RootFS(dest.parent);parent.path(dest.name)
    if dest.exists():
        fs=RootFS(dest)
        require(all(fs.read(k)==v for k,v in files.items()),'occupied_installation','Destino ocupado/modificado; não sobrescrever.',3)
        existing={f.relative_to(dest).as_posix() for f in dest.rglob('*') if f.is_file() and '__pycache__' not in f.parts}
        require(existing==set(files),'occupied_installation','Destino contém customizações; não declarar instalação equivalente.',3)
        return result('Pacote já instalado com os mesmos bytes; no-op.')
    stage=dest.parent/('.omnx-install-'+uuid.uuid4().hex)
    stage.mkdir(mode=0o700);fs=RootFS(stage)
    # On interruption this isolated staging remains inert, destination is not active.
    for path,raw in files.items():fs.write(path,raw,None,0o644)
    require(not dest.exists() and not dest.is_symlink(),'installation_race','Destino apareceu durante instalação.',3)
    os.rename(stage,dest)
    return result('Pacote extraído e verificado. Ativação no host é separada.',changed_paths=[str(dest)],limitations=['Checksum não é assinatura. Nenhum script do pacote foi executado; instalação anterior não foi alterada.'])
