"""Scoped checkpoints; metadata and hints never become task authority."""
from .core import *
from .project import ensure_writable
from .tasks import Store
from .audit import snapshot

def save(fs,session_id,task_id,paths,next_action,temporary_context='',expected=None):
    c=ensure_writable(fs)
    require(re.fullmatch(r'[A-Za-z][A-Za-z0-9-]{2,100}',session_id) is not None,'invalid_session','ID de sessão inválido.')
    path,m,body=Store(fs).get(task_id)
    require(m['status'] not in ('done','cancelled'),'inactive_task','Task terminal não precisa de checkpoint ativo.',3)
    wid=digest(str(fs.root).encode());target=f'.omnx/local/sessions/{wid}/{session_id}/checkpoint.json'
    cp={'schema_version':1,'project_id':c['project_id'],'worktree_id':wid,'session_id':session_id,'task_id':task_id,'task_sha256':fs.hash(path),'snapshot':snapshot(fs,paths),'next_action':next_action,'temporary_context':temporary_context,'created_at':now()}
    validate(cp,schema('checkpoint'))
    with metadata_lock(fs):fs.write(target,json_bytes(cp),expected)
    return result('Checkpoint local gravado, sem backlog paralelo.',changed_paths=[target],checkpoint=cp,sha256=digest(json_bytes(cp)))

def check(fs,session_id):
    c=ensure_writable(fs);wid=digest(str(fs.root).encode());target=f'.omnx/local/sessions/{wid}/{session_id}/checkpoint.json'
    cp=fs.data(target);require(cp is not None,'missing_checkpoint','Checkpoint desta worktree/sessão ausente.',4);validate(cp,schema('checkpoint'))
    require(cp['project_id']==c['project_id'] and cp['worktree_id']==wid,'wrong_checkpoint','Checkpoint de outro projeto/worktree.',3)
    p,m,_=Store(fs).get(cp['task_id']);s=cp['snapshot'];new=snapshot(fs,[x['path'] for x in s['files']],s['environment'],s['environment_config_digest'],s['environment_observed'])
    reusable=fs.hash(p)==cp['task_sha256'] and new['content_digest']==s['content_digest'] and m['status'] not in ('done','cancelled') and m['authorization']['status']=='authorized'
    return result('Checkpoint precisa ser comparado com a Task e o estado real.',reusable=reusable,checkpoint=cp,current_task_status=m['status'])
