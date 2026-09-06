"""A Markdown file per task. Task existence is not execution authorization."""
from __future__ import annotations
from copy import deepcopy
import datetime as dt
from pathlib import Path
import re
from .core import *

TRANSITIONS={
 'backlog':{'ready','cancelled'}, 'ready':{'in_progress','blocked','cancelled'},
 'in_progress':{'blocked','review','cancelled'}, 'blocked':{'ready','in_progress','cancelled'},
 'review':{'done','in_progress','blocked','cancelled'},'done':{'in_progress'},'cancelled':set()}

def parse(raw):
    require(raw is not None,'missing_task','Task não encontrada.',4)
    try: text=raw.decode('utf-8-sig')
    except UnicodeError: raise MethodError('invalid_task','Task deve estar em UTF-8.') from None
    # Parse only the frontmatter delimiter, then use a strict YAML parser.
    lines=text.splitlines(keepends=True)
    require(lines and lines[0].strip()=='---','invalid_task','Frontmatter da Task ausente.')
    end=next((i for i in range(1,len(lines)) if lines[i].strip()=='---'),None)
    require(end is not None,'invalid_task','Frontmatter não foi fechado.')
    meta=load_data(''.join(lines[1:end]),yaml_ok=True)
    validate(meta,schema('task'))
    timestamp(meta['created_at']); timestamp(meta['updated_at'])
    body=''.join(lines[end+1:]).lstrip('\r\n')
    require(bool(body.strip()),'invalid_task','Task precisa de escopo no corpo.')
    check_meta(meta)
    return meta,body

def dump(meta,body):
    validate(meta,schema('task')); check_meta(meta)
    timestamp(meta['created_at']); timestamp(meta['updated_at'])
    # JSON is a strict YAML subset, avoids implicit YAML type changes, remains readable.
    return b'---\n'+json_bytes(meta)+b'---\n\n'+body.encode('utf-8').rstrip()+b'\n'

def check_meta(meta):
    au=meta['authorization']
    if au['status'] in ('authorized','revoked'):
        require(bool(au['basis_ref']),'missing_authority','Autorização/revogação exige origem explícita.')
    if meta['status'] in ('ready','in_progress','review','done'):
        require(au['status']=='authorized','unauthorized_task','Task não tem autorização válida.',5)
    if meta['status']=='in_progress': require(bool(meta.get('owner')),'missing_owner','Assuma responsabilidade pela Task.')
    if meta['status']=='blocked': require(bool(meta.get('blocked_reason')),'missing_reason','Bloqueio exige causa específica.')
    if meta['status']=='cancelled': require(bool(meta.get('cancel_reason')),'missing_reason','Cancelamento exige motivo.')
    if meta['status']=='done':
        c=meta.get('closure')
        require(c is not None,'missing_closure','Conclusão exige evidência e local de entrega.')
        require(c['scope_met'] and c['diff_reviewed'] and not c['known_regression'],'incomplete_task','Critérios de conclusão não satisfeitos.',5)
        require(not any(e['result']=='fail' for e in c['evidence']),'failed_evidence','Há evidência de falha na conclusão.',5)
        if meta.get('impact',{}).get('security')=='S3':
            require(any(e['result']=='pass' for e in c['evidence']),'missing_evidence','S3 não pode concluir sem evidência positiva pertinente.',5)
        require(c['delivery']!='production' or c['authority_ref'].startswith('release:'),'missing_release','Entrega em produção exige referência release: verificável.',5)

class Store:
    def __init__(self,fs): self.fs=fs
    def entries(self):
        root=self.fs.path('.omnx/tasks')
        if not root.exists(): return []
        out=[]; seen=set()
        for p in sorted(root.rglob('TASK-*.md')):
            rel=p.relative_to(self.fs.root).as_posix()
            meta,body=parse(self.fs.read(rel))
            require(p.name==meta['id']+'.md','task_filename','ID e nome do arquivo divergem.')
            require(meta['id'] not in seen,'duplicate_task','ID de Task duplicado; reconcilie antes de escrever.',3)
            seen.add(meta['id']);out.append((rel,meta,body))
        return out
    def get(self,task_id):
        require(re.fullmatch(r'TASK-[A-Za-z0-9][A-Za-z0-9-]{1,90}',task_id) is not None,'invalid_id','ID de Task inválido.')
        matches=[x for x in self.entries() if x[1]['id']==task_id]
        require(len(matches)==1,'missing_task','Task não encontrada.',4)
        return matches[0]
    def graph(self,candidate=None):
        metas={m['id']:m for _,m,_ in self.entries()}
        if candidate: metas[candidate['id']]=candidate
        for tid,m in metas.items():
            require(all(d in metas for d in m.get('depends_on',[])),'missing_dependency','Dependência não encontrada.')
        visiting=set();done=set()
        def visit(t):
            require(t not in visiting,'dependency_cycle','Dependências de Tasks formam ciclo.',3)
            if t in done:return
            visiting.add(t)
            for d in metas[t].get('depends_on',[]):visit(d)
            visiting.remove(t);done.add(t)
        for t in metas:visit(t)
        return metas
    def create(self,payload,body):
        from .project import ensure_writable
        ensure_writable(self.fs)
        require(isinstance(payload,dict),'invalid_task','Payload de Task inválido.')
        with metadata_lock(self.fs):
            ensure_writable(self.fs)
            m={'schema_version':1,'id':new_id('TASK'),'status':'backlog','authorization':{'status':'proposed','basis_ref':None},'created_at':now(),'updated_at':now(),**payload}
            require(m['status'] in ('backlog','ready'),'invalid_initial_state','Task nova começa em backlog ou ready.')
            raw=dump(m,body)
            require(not any(x[1]['id']==m['id'] for x in self.entries()),'duplicate_task','ID já existe.',3)
            self.graph(m)
            path='.omnx/tasks/'+m['id']+'.md'
            self.fs.write(path,raw,None)
        return result('Task criada; sua autorização permanece explícita.',changed_paths=[path],task=m,sha256=digest(raw))
    def update(self,tid,patch,expected,*,body=None,transition=None,authority_ref=None):
        from .project import ensure_writable
        ensure_writable(self.fs)
        with metadata_lock(self.fs):
            ensure_writable(self.fs)
            path,old,oldbody=self.get(tid)
            require(self.fs.hash(path)==expected,'stale_state','Task mudou; releia antes de atualizar.',3)
            require('/archive/' not in path,'archived_task','Task arquivada é histórica; restaure explicitamente antes de reabrir.',3)
            require(not(set(patch)&{'id','schema_version','created_at','updated_at','status'}),'immutable_field','Campo gerenciado ou estado deve ser alterado pela operação correspondente.')
            if old.get('owner') and 'owner' in patch and patch['owner']!=old['owner'] and old['status']=='in_progress':
                require(bool(authority_ref),'owner_transfer_required','Transferir Task ativa exige origem explícita.',5)
            m={**old,**patch,'updated_at':now()}
            if 'authorization' in patch and patch['authorization']!=old['authorization']:
                require(bool(authority_ref),'missing_authority','Alteração de autorização exige --authority-ref.',5)
                require(patch['authorization']['basis_ref']==authority_ref,'authority_mismatch','A origem declarada deve corresponder à autoridade fornecida.')
            if transition:
                require(transition in TRANSITIONS[old['status']],'invalid_transition','Transição de estado inválida.')
                if transition=='cancelled' or old['status']=='done':require(bool(authority_ref),'missing_authority','Cancelar/reabrir exige origem explícita.',5)
                m['status']=transition
                if transition not in ('done',): m['closure']=None
                if transition not in ('blocked',):m['blocked_reason']=None
            if m['authorization']['status']=='revoked' and m['status'] in ('ready','in_progress','review'):
                m['status']='blocked';m['blocked_reason']='Autorização revogada.'
            metas=self.graph(m)
            if m['status'] in ('in_progress','review','done'):
                require(all(metas[d]['status']=='done' for d in m.get('depends_on',[])),'dependency_not_done','Há dependência ainda não concluída.',5)
            raw=dump(m,oldbody if body is None else body)
            self.fs.write(path,raw,expected)
        return result('Task atualizada com controle de concorrência.',changed_paths=[path],task=m,sha256=digest(raw))
    def archive(self,tid,expected):
        from .project import ensure_writable
        ensure_writable(self.fs)
        with metadata_lock(self.fs):
            path,m,body=self.get(tid)
            require(m['status'] in ('done','cancelled'),'not_terminal','Só Tasks terminais podem ser arquivadas.')
            require(self.fs.hash(path)==expected,'stale_state','Task mudou antes do arquivamento.',3)
            if '/archive/' in path:return result('Task já arquivada; nenhuma alteração.')
            dest=f'.omnx/tasks/archive/{now()[:7]}/{tid}.md'
            raw=self.fs.read(path)
            # Single-filesystem rename keeps the ID and bytes; no duplicate interval.
            require(self.fs.hash(dest) is None,'archive_conflict','Destino de arquivo já existe.',3)
            with self.fs.parent(path) as (sfd,sname,sp),self.fs.parent(dest,True) as (dfd,dname,dp):
                require(self.fs.hash(path)==expected,'stale_state','Task mudou durante arquivamento.',3)
                if sfd is not None:os.rename(sname,dname,src_dir_fd=sfd,dst_dir_fd=dfd);os.fsync(sfd);os.fsync(dfd)
                else:os.rename(sp/sname,dp/dname)
        return result('Task arquivada; ID continua resolvível.',changed_paths=[path,dest])
