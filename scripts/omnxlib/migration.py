"""Frozen semantic plans; deterministic CAS apply/resume/rollback.

The engine does not pretend to infer product decisions from prose. The agent
prepares explicit resolutions, and a caller explicitly approves the plan digest.
"""
from __future__ import annotations
import base64
from .core import *
from .project import AGENTS, default_config, default_lock, config, pending, git

DENIED={'node_modules','vendor','.git','.venv','dist','build','__pycache__','local','archive','migrations'}
CATEGORIES={'instruction','requirement','initiative','task','architecture','decision','guide','session','history','obsolete_template'}

def allowed(path):
    portable_path(path)
    require(not any(p in DENIED for p in path.split('/')),'protected_path','Migração não pode escrever em histórico, dependências ou estado privado.')
    require(path in ('AGENTS.md','CLAUDE.md','.gitignore','CHANGELOG.md') or
        (path.startswith('docs/') and path.lower().endswith(('.md','.json','.yaml','.yml'))) or
        (path.startswith('.omnx/') and path.lower().endswith(('.md','.json','.yaml','.yml'))) or
        path=='.empire/state.json','migration_scope','Path não pertence aos metadados suportados pelo método.')
    require(path not in ('.omnx/security/policy.json',),'protected_policy','Migração não concede nova política de aprovação.')
    return path

def blocks(raw):
    """Split UTF-8 Markdown at headings outside code fences; exact bytes cover all input."""
    try: text=raw.decode('utf-8')
    except UnicodeError:raise MethodError('encoding_review','Arquivo não UTF-8 requer conversão autorizada separada.') from None
    lines=text.splitlines(keepends=True); starts=[0];fence=None
    for i,line in enumerate(lines):
        stripped=line.lstrip()
        if stripped.startswith(('```','~~~')):
            mark=stripped[:3]
            if fence is None:fence=mark
            elif fence==mark:fence=None
        elif fence is None and re.match(r'^#{1,6}\s',line) and i>0:starts.append(i)
    starts.append(len(lines));out=[]
    for n,(a,b) in enumerate(zip(starts,starts[1:])):
        data=''.join(lines[a:b]).encode('utf-8')
        if data:out.append({'id':f'B-{n:04d}-{digest(data)[:16]}','sha256':digest(data),'start_line':a+1,'end_line':b,'raw':data})
    require(b''.join(x['raw'] for x in out)==raw,'block_partition','Partição de conteúdo inválida.')
    return out

def inventory(fs,paths=None):
    if paths is None:
        paths=[p for p in ('AGENTS.md','CLAUDE.md','.empire/state.json','.omnx/state.json','.omnx/TASKS.md') if fs.read(p) is not None]
        docs=fs.path('docs')
        if docs.exists():
            for p in sorted(docs.rglob('*.md')):
                rel=p.relative_to(fs.root).as_posix()
                if not any(x in DENIED for x in rel.split('/')) and len(paths)<3000: paths.append(rel)
    require(isinstance(paths,list) and len(set(paths))==len(paths),'invalid_sources','Sources devem ser lista sem duplicatas.')
    out=[]
    for path in sorted(paths):
        allowed(path);raw=fs.read(path)
        require(raw is not None,'missing_source','Fonte selecionada não existe.',4,path=path)
        out.append({'path':path,'sha256':digest(raw),'blocks':[{k:v for k,v in b.items() if k!='raw'} for b in blocks(raw)]})
    return result('Inventário candidato, sem mutação e sem inferir propriedade por nome.',sources=out,limitations=['Selecione somente arquivos governados. Semântica requer resolução explícita; títulos não provam estado nem autorização.'])

def seal(plan):
    x={k:v for k,v in plan.items() if k!='plan_digest'};plan['plan_digest']=object_digest(x);return plan

def _raw(op):
    if op['action']=='delete':
        require(op['after_base64'] is None and op['after_sha256'] is None,'invalid_delete','Remoção não deve ter saída.');return None
    try:out=base64.b64decode(op['after_base64'],validate=True)
    except (ValueError,TypeError):raise MethodError('invalid_asset','Asset base64 inválido.') from None
    require(len(out)<=MAX_DOCUMENT and digest(out)==op['after_sha256'],'invalid_asset','Asset excede limite ou hash diverge.')
    return out

def validate_plan(fs,plan):
    validate(plan,schema('migration-plan'))
    require(plan['plan_digest']==object_digest({k:v for k,v in plan.items() if k!='plan_digest'}),'tampered_plan','Digest do plano não corresponde.')
    require(plan['root_identity']==digest(str(fs.root).encode()),'wrong_root','Plano pertence a outra raiz.',3)
    require(len({s['path'] for s in plan['sources']})==len(plan['sources']),'duplicate_source','Fonte duplicada.')
    sources={x['path']:x['sha256'] for x in plan['sources']}
    targets=[];ids=[]
    for op in plan['operations']:
        allowed(op['path']);fs.path(op['path']);targets.append(op['path'].casefold());ids.append(op['id']);_raw(op)
        require(op['mode'] in (0o600,0o644),'invalid_mode','Somente permissões de arquivo não executável são permitidas.')
        if op['before_sha256'] is not None:
            require(sources.get(op['path'])==op['before_sha256'],'unbacked_operation','Arquivo sobrescrito/removido deve constar no inventário do plano.')
        if op['action']=='delete':require(op['before_sha256'] is not None,'invalid_delete','Remoção exige arquivo preexistente.')
    require(len(set(targets))==len(targets) and len(set(ids))==len(ids),'duplicate_operation','Destinos/IDs duplicados ou colisão de caixa.')
    # These checks do not establish semantic correctness or identity of approver.
    return plan

def make_plan(fs,authority_ref,bootstrap_ref,*,resolutions=None):
    require(authority_ref and bootstrap_ref,'missing_authority','Planejamento aplicável exige origem de autorização e evidência do bootstrap selecionado.')
    require(not pending(fs),'migration_pending','Retome a migração incompleta antes de planejar outra.',5)
    existing=fs.read('.omnx/project.yaml')
    if existing is not None and resolutions is None:
        c=config(fs)
        if fs.read('CLAUDE.md') is None and fs.read('.omnx/TASKS.md') is None:
            return result('Projeto já no schema atual; nenhuma reorganização automática.',noop=True)
    governed=[p for p in ('AGENTS.md','CLAUDE.md','.empire/state.json','.omnx/state.json','.omnx/TASKS.md') if fs.read(p) is not None]
    if resolutions is None and governed:
        return {**inventory(fs),'status':'needs_review','code':'SEMANTIC_RESOLUTION_REQUIRED','summary':'Conteúdo existente exige mapeamento antes de substituir instruções. Use references/migration.md.'}
    c=config(fs) if existing else default_config(fs)
    sources=[];mappings=[];writes={};source_blocks={}
    if resolutions is not None:
        require(isinstance(resolutions,dict) and set(resolutions)=={'source_paths','mappings','writes'},'invalid_resolutions','Resolução exige source_paths, mappings, writes.')
        inv=inventory(fs,resolutions['source_paths'])
        sources=[{'path':s['path'],'sha256':s['sha256']} for s in inv['sources']]
        require(set(governed)<=set(resolutions['source_paths']),'unmapped_governance','Entradas governantes existentes ficaram fora da resolução.')
        for s in sources:
            for b in blocks(fs.read(s['path'])):source_blocks[(s['path'],b['id'])]=b
        require(isinstance(resolutions['writes'],dict),'invalid_writes','Writes deve mapear paths para texto UTF-8.')
        for path,text in resolutions['writes'].items():
            allowed(path);require(type(text)is str,'invalid_asset','Texto de destino deve ser string.')
            require(path.rsplit('/',1)[-1].lower()!='claude.md','legacy_target','Não criar outra entrada CLAUDE.md governada.')
            require(path not in ('CLAUDE.md','.omnx/state.json','.omnx/TASKS.md','.empire/state.json','.omnx/method.lock.json','.omnx/project.yaml','.gitignore'),'legacy_target','Destino legado ou gerenciado não pode ser recriado.')
            require(fs.read(path) is None or path in resolutions['source_paths'],'unowned_destination','Destino existente deve ser inventariado antes de alteração.',3)
            writes[path]=text.encode('utf-8')
        seen=set()
        for mapping in resolutions['mappings']:
            validate(mapping,schema('migration-plan')['properties']['mappings']['items'])
            key=(mapping['source_path'],mapping['block_id'])
            require(key in source_blocks and key not in seen,'invalid_mapping','Bloco inexistente ou duplicado.');seen.add(key)
            b=source_blocks[key];require(mapping['block_sha256']==b['sha256'],'stale_block','Bloco mudou.',3)
            dest=mapping['destination']; treatment=mapping['treatment']
            if treatment=='preserve':
                require(dest in writes and b['raw'] in writes[dest],'lost_content','Bloco marcado preserve não está integralmente no destino.')
            else:
                require(bool(mapping['decision_ref']),'unreviewed_semantics','Transformação semântica exige decisão/revisão explícita.',5)
                if treatment=='replace':require(dest in writes,'missing_destination','Substituição exige destino ativo.')
            if mapping['category']=='instruction':
                require(treatment in ('preserve','replace') and dest is not None,'inactive_custom_rule','Instrução ativa não pode ser escondida só no backup.',5)
                require(dest=='AGENTS.md' or dest.encode() in writes.get('AGENTS.md',b''),'unlinked_instruction','Referência de instrução deve ser alcançável por AGENTS.md.')
            if mapping['category']=='task' and treatment not in ('supersede','history'):
                require(dest and dest.startswith('.omnx/tasks/TASK-') and dest.endswith('.md'),'task_destination','Trabalho ativo deve migrar ao Task Store.')
            mappings.append(mapping)
        require(seen==set(source_blocks),'unmapped_blocks','Existem blocos sem destino/decisão; não prosseguir.',5)
        require('AGENTS.md' in writes,'missing_agents','Resolução deve produzir AGENTS.md canônico.')
    else:writes['AGENTS.md']=AGENTS.encode('utf-8')
    mid='MIG-'+uuid.uuid4().hex[:24]
    writes['.omnx/project.yaml']=json_bytes(c)
    lock=default_lock(mid)
    old_lock=fs.data('.omnx/method.lock.json')
    if old_lock is not None:
        validate(old_lock,schema('method-lock'))
        lock['adopted_packages']['security-auditor']=old_lock['adopted_packages'].get('security-auditor')
    writes['.omnx/method.lock.json']=json_bytes(lock)
    gi=fs.read('.gitignore') or b''
    if b'.omnx/local/' not in gi:writes['.gitignore']=gi+(b'\n' if gi and not gi.endswith(b'\n') else b'')+b'\n# OMNX: local restricted state\n.omnx/local/\n'
    # Capture ALL overwritten originals, including configuration and gitignore.
    known={s['path'] for s in sources}
    for path in writes:
        old=fs.read(path)
        if old is not None and path not in known:sources.append({'path':path,'sha256':digest(old)});known.add(path)
    operations=[]
    # Final lock is last. Entry consolidation can then be rolled back as one journaled set.
    for path in sorted(set(writes)|{s['path'] for s in sources},key=lambda p:(p=='.omnx/method.lock.json',p)):
        before=fs.hash(path);after=writes.get(path)
        # Generated config/gitignore are not removed by the semantic source selection.
        if after is None and path not in (resolutions or {}).get('source_paths',[]):continue
        if after is not None and before==digest(after):continue
        op={'id':f'OP-{len(operations)+1:04d}','action':'delete' if after is None else 'write','path':path,'before_sha256':before,'after_sha256':digest(after) if after is not None else None,'after_base64':base64.b64encode(after).decode() if after is not None else None,'mode':0o600}
        operations.append(op)
    plan=seal({'schema_version':1,'migration_id':mid,'plan_digest':'0'*64,'root_identity':digest(str(fs.root).encode()),'project_id':c['project_id'],'kind':'legacy' if governed else 'init','sources':sources,'mappings':mappings,'operations':operations,'authority_ref':authority_ref,'bootstrap':{'mode':'explicit_skill','evidence_ref':bootstrap_ref},'limitations':['A equivalência semântica e a autoridade declarada devem ser revisadas pelo usuário/agente no contexto confiável. O motor verifica estrutura, cobertura e preservação, não intenção humana.']})
    validate_plan(fs,plan);validate_outputs(plan)
    return plan

def validate_outputs(plan):
    from .tasks import parse
    outputs={op['path']:_raw(op) for op in plan['operations'] if op['action']=='write'}
    for path,raw in outputs.items():
        if path=='.omnx/project.yaml':validate(load_data(raw,yaml_ok=True),schema('project'))
        elif path=='.omnx/method.lock.json':validate(load_data(raw),schema('method-lock'))
        elif path.startswith('.omnx/tasks/TASK-'):
            m,_=parse(raw);require(path.rsplit('/',1)[1]==m['id']+'.md','task_filename','Task migrada possui ID divergente.')
    require('CLAUDE.md' not in outputs,'legacy_target','Nova entrada CLAUDE.md proibida.')

def _base(mid):
    require(re.fullmatch(r'MIG-[a-f0-9]{24}',mid) is not None,'invalid_id','ID de migração inválido.')
    return '.omnx/local/migrations/'+mid

def status(fs,mid):
    j=fs.data(_base(mid)+'/journal.json')
    require(j is not None,'missing_journal','Journal não encontrado.',4);validate(j,schema('migration-journal'));return j

def _save(fs,base,j):
    j['updated_at']=now();validate(j,schema('migration-journal'))
    fs.write(base+'/journal.json',json_bytes(j),fs.hash(base+'/journal.json'))

def apply(fs,plan,approved_digest,*,resume=False,fault=None):
    fault=fault or (lambda point:None)
    validate_plan(fs,plan);validate_outputs(plan)
    require(approved_digest==plan['plan_digest'],'unapproved_plan','Confirme o digest do plano revisado; nada será aplicado.',5)
    base=_base(plan['migration_id'])
    with metadata_lock(fs):
        others=[m for m in pending(fs) if m!=plan['migration_id']]
        require(not others,'migration_pending','Outra migração está incompleta.',5)
        j=fs.data(base+'/journal.json')
        if j:
            validate(j,schema('migration-journal'));require(j['plan_digest']==plan['plan_digest'],'journal_conflict','Journal pertence a outro plano.',3)
            if j['phase']=='applied':return result('Migração já aplicada; no-op.',migration_id=plan['migration_id'])
            require(resume,'resume_required','Migração iniciada; use resume.',3)
            require(j['phase'] not in ('rolling_back','rolled_back'),'rollback_state','Migração está em recuperação; não aplicar novamente.',3)
        else:
            # Preflight before ANY canonical writes.
            for s in plan['sources']:require(fs.hash(s['path'])==s['sha256'],'stale_plan','Fonte mudou desde o planejamento.',3,path=s['path'])
            for op in plan['operations']:require(fs.hash(op['path'])==op['before_sha256'],'stale_plan','Destino mudou desde o planejamento.',3,path=op['path'])
            require(not git(fs,['ls-files','--','.omnx/local']),'tracked_private_state','Área privada já está rastreada; resolva antes de criar backups.',5)
            fs.write(base+'/plan.json',json_bytes(plan),None)
            j={'schema_version':1,'migration_id':plan['migration_id'],'plan_digest':plan['plan_digest'],'phase':'preparing','snapshot_ready':False,'completed_ops':[],'rollback_ops':[],'created_at':now(),'updated_at':now()};_save(fs,base,j);fault('journal_created')
        if not j['snapshot_ready']:
            for op in plan['operations']:
                require(fs.hash(op['path'])==op['before_sha256'],'stale_plan','Origem mudou antes do snapshot completo.',3,path=op['path'])
                if op['before_sha256'] is not None:
                    p=base+'/backup/'+op['id']+'.bin';raw=fs.read(op['path'])
                    if fs.read(p) is None:fs.write(p,raw,None)
                    require(fs.hash(p)==op['before_sha256'],'backup_corrupt','Backup não corresponde à origem.',5)
                if op['action']=='write':
                    p=base+'/staging/'+op['id']+'.bin';raw=_raw(op)
                    if fs.read(p) is None:fs.write(p,raw,None)
                    require(fs.hash(p)==op['after_sha256'],'staging_corrupt','Staging não corresponde ao plano.',5)
                fault('snapshot:'+op['id'])
            j['snapshot_ready']=True;j['phase']='snapshotted';_save(fs,base,j);fault('snapshot_ready')
        # Verify backups before any destructive or resumed mutation.
        for op in plan['operations']:
            if op['before_sha256'] is not None:require(fs.hash(base+'/backup/'+op['id']+'.bin')==op['before_sha256'],'backup_corrupt','Backup inválido; originais não serão removidos.',5)
        j['phase']='applying';_save(fs,base,j)
        for op in plan['operations']:
            cur=fs.hash(op['path']);before=op['before_sha256'];after=op['after_sha256']
            require(cur in (before,after),'stale_state','Arquivo foi editado fora desta migração; preserve e reconcilie.',3,path=op['path'])
            if cur!=after:
                fault('before:'+op['id'])
                if op['action']=='write':
                    raw=fs.read(base+'/staging/'+op['id']+'.bin');require(raw is not None and digest(raw)==after,'staging_corrupt','Staging inválido.',5);fs.write(op['path'],raw,before,op['mode'])
                else:fs.delete(op['path'],before)
                fault('after:'+op['id'])
            if op['id'] not in j['completed_ops']:j['completed_ops'].append(op['id'])
            _save(fs,base,j)
        for op in plan['operations']:require(fs.hash(op['path'])==op['after_sha256'],'postcheck_failed','Pós-condição de migração falhou.',3)
        c=config(fs)
        require(c['project_id']==plan['project_id'],'postcheck_failed','Identidade do projeto diverge do plano.',3)
        lock=fs.data('.omnx/method.lock.json');validate(lock,schema('method-lock'))
        require(lock['last_migration_id']==plan['migration_id'],'postcheck_failed','Lock não registra a migração aplicada.',3)
        require(bool(fs.read('AGENTS.md')) and fs.read('CLAUDE.md') is None and fs.read('.omnx/TASKS.md') is None,'active_legacy_source','Fonte canônica ausente ou entrada legada ativa; migração não está concluída.',5)
        from .tasks import Store
        Store(fs).graph()
        report={'migration_id':plan['migration_id'],'plan_digest':plan['plan_digest'],'result':'applied','paths':[{'path':o['path'],'action':o['action'],'before':o['before_sha256'],'after':o['after_sha256']} for o in plan['operations']],'limitations':plan['limitations']}
        rp='.omnx/migrations/'+plan['migration_id']+'/report.json'
        if fs.read(rp) is None:fs.write(rp,json_bytes(report),None)
        else:require(fs.read(rp)==json_bytes(report),'report_conflict','Relatório existente diverge.',3)
        j['phase']='applied';_save(fs,base,j);fault('finalized')
        return result('Migração aplicada e hashes verificados.',changed_paths=[o['path'] for o in plan['operations']],migration_id=plan['migration_id'],recovery_ref=base+'/journal.json',limitations=plan['limitations'])

def resume(fs,mid,approved_digest):
    plan=fs.data(_base(mid)+'/plan.json');require(plan is not None,'missing_plan','Plano recuperável ausente.',4)
    return apply(fs,plan,approved_digest,resume=True)

def rollback(fs,mid,approved_digest,*,fault=None):
    fault=fault or (lambda point:None);base=_base(mid)
    with metadata_lock(fs):
        plan=fs.data(base+'/plan.json');require(plan is not None,'missing_plan','Plano não encontrado.',4);validate_plan(fs,plan)
        require(approved_digest==plan['plan_digest'],'unapproved_plan','Rollback exige digest do plano revisado.',5)
        j=status(fs,mid)
        if j['phase']=='rolled_back':return result('Rollback já concluído; no-op.')
        if any(o['path']=='.omnx/project.yaml' and o['before_sha256'] is None for o in plan['operations']):
            planned={o['path'] for o in plan['operations']}
            taskroot=fs.path('.omnx/tasks')
            later=[p for p in taskroot.rglob('TASK-*.md') if p.relative_to(fs.root).as_posix() not in planned] if taskroot.exists() else []
            require(not later,'rollback_dependents','Novas Tasks dependem desta adoção. Preserve/reconcilie antes de remover a configuração.',3)
        # Preflight all files prevents predictable partial rollback on a user edit.
        for op in plan['operations']:
            require(fs.hash(op['path']) in (op['before_sha256'],op['after_sha256']),'rollback_conflict','Há edição posterior; rollback não a sobrescreverá.',3,path=op['path'])
            if op['before_sha256'] is not None and fs.hash(op['path'])!=op['before_sha256']:
                require(fs.hash(base+'/backup/'+op['id']+'.bin')==op['before_sha256'],'backup_corrupt','Backup necessário inválido.',5)
        j['phase']='rolling_back';_save(fs,base,j)
        for op in reversed(plan['operations']):
            cur=fs.hash(op['path'])
            if cur!=op['before_sha256']:
                if op['before_sha256'] is None:fs.delete(op['path'],op['after_sha256'])
                else:fs.write(op['path'],fs.read(base+'/backup/'+op['id']+'.bin'),op['after_sha256'],op['mode'])
                fault('rollback:'+op['id'])
            if op['id'] not in j['rollback_ops']:j['rollback_ops'].append(op['id'])
            _save(fs,base,j)
        j['phase']='rolled_back';_save(fs,base,j)
    return result('Arquivos da migração restaurados. Backups/journal permanecem restritos.',changed_paths=[o['path'] for o in plan['operations']],recovery_ref=base+'/journal.json')
