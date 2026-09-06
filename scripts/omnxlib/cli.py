"""Explicit CLI. No network calls, background work, auto-deploy or hidden setup."""
from __future__ import annotations
import argparse
import subprocess
from .core import *

def parser():
    p=argparse.ArgumentParser(description='OMNX local runtime — defaults do not mutate applications.')
    p.add_argument('--root',help='Raiz de governança explícita; não inferida pelo cwd.')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor')
    sub.add_parser('verify-package')
    md=sub.add_parser('method').add_subparsers(dest='action',required=True)
    q=md.add_parser('verify');q.add_argument('--auditor-dir')
    q=md.add_parser('adopt');q.add_argument('--expected-sha256',required=True);q.add_argument('--authority-ref',required=True);q.add_argument('--auditor-dir');q.add_argument('--trusted-auditor-digest')
    r=sub.add_parser('route');r.add_argument('--ux',choices=['UX0','UX1','UX2','UX3'],required=True);r.add_argument('--security',choices=['S0','S1','S2','S3'],required=True);r.add_argument('--operation',choices=['O0','O1','O2','O3'],required=True)
    i=sub.add_parser('init');i.add_argument('--authority-ref',required=True);i.add_argument('--bootstrap-ref',required=True);i.add_argument('--output')
    t=sub.add_parser('task').add_subparsers(dest='action',required=True)
    l=t.add_parser('list');l.add_argument('--status');l.add_argument('--authorization')
    s=t.add_parser('show');s.add_argument('id')
    c=t.add_parser('create');c.add_argument('--data',required=True);c.add_argument('--body-file',required=True)
    for action in ('update','transition'):
        q=t.add_parser(action);q.add_argument('id');q.add_argument('--expected-sha256',required=True);q.add_argument('--data');q.add_argument('--body-file');q.add_argument('--authority-ref')
        if action=='transition':q.add_argument('--to',required=True)
    a=t.add_parser('archive');a.add_argument('id');a.add_argument('--expected-sha256',required=True)
    m=sub.add_parser('migrate').add_subparsers(dest='action',required=True)
    inv=m.add_parser('inventory');inv.add_argument('--paths',nargs='*');inv.add_argument('--output')
    mp=m.add_parser('plan');mp.add_argument('--resolutions');mp.add_argument('--authority-ref',required=True);mp.add_argument('--bootstrap-ref',required=True);mp.add_argument('--output')
    ap=m.add_parser('apply');ap.add_argument('--plan',required=True);ap.add_argument('--approved-digest',required=True)
    for a in ('resume','rollback'):
        q=m.add_parser(a);q.add_argument('id');q.add_argument('--approved-digest',required=True)
    st=m.add_parser('status');st.add_argument('id')
    a=sub.add_parser('audit').add_subparsers(dest='action',required=True)
    q=a.add_parser('catalog');q.add_argument('--family')
    q=a.add_parser('snapshot');q.add_argument('--paths',nargs='+',required=True);q.add_argument('--environment',default='local');q.add_argument('--output')
    q=a.add_parser('request');q.add_argument('--paths',nargs='+',required=True);q.add_argument('--controls',nargs='*',default=[]);q.add_argument('--surfaces',nargs='*',default=[]);q.add_argument('--objective',required=True);q.add_argument('--impact',choices=['S0','S1','S2','S3'],default='S2');q.add_argument('--mode',choices=['design','delta','full'],default='delta');q.add_argument('--task-id');q.add_argument('--orchestrator-id');q.add_argument('--environment',default='local');q.add_argument('--environment-digest');q.add_argument('--environment-observed',action='store_true');q.add_argument('--output')
    for action in ('validate-request','response-template','validate-response','persist'):
        q=a.add_parser(action);q.add_argument('--request',required=True);q.add_argument('--output')
        if action in ('validate-response','persist'):q.add_argument('--response',required=True)
    q=a.add_parser('scan');q.add_argument('--paths',nargs='+',required=True)
    q=sub.add_parser('gate');q.add_argument('--request',required=True);q.add_argument('--response',required=True);q.add_argument('--operation',choices=['local_edit','commit','merge','deploy'],required=True);q.add_argument('--environment',required=True);q.add_argument('--authority-ref');q.add_argument('--environment-digest')
    u=sub.add_parser('update').add_subparsers(dest='action',required=True)
    for action in ('check','plan'):
        q=u.add_parser(action);q.add_argument('--archive',required=True);q.add_argument('--expected-sha256',required=True);q.add_argument('--current-version');q.add_argument('--destination',required=True);q.add_argument('--output')
    q=u.add_parser('apply');q.add_argument('--plan',required=True);q.add_argument('--approved-digest',required=True)
    s=sub.add_parser('session').add_subparsers(dest='action',required=True)
    q=s.add_parser('check');q.add_argument('id')
    q=s.add_parser('save');q.add_argument('id');q.add_argument('--task-id',required=True);q.add_argument('--paths',nargs='+',required=True);q.add_argument('--next-action',required=True);q.add_argument('--context',default='');q.add_argument('--expected-sha256')
    q=sub.add_parser('host');q.add_argument('name',choices=['claude','codex']);q.add_argument('--execute',action='store_true');q.add_argument('--trust-root',action='store_true');q.add_argument('--expected-agents-sha256');q.add_argument('host_args',nargs=argparse.REMAINDER)
    return p

def read_text(path):
    p=Path(path).absolute();raw=RootFS(p.parent).read(p.name)
    require(raw is not None,'missing_file','Arquivo de texto não encontrado.',4)
    try:return raw.decode('utf-8')
    except UnicodeError:raise MethodError('encoding','Arquivo precisa ser UTF-8.') from None

def verify_package():
    idx=load_data((PACKAGE/'integrity.json').read_bytes())
    require(idx.get('algorithm')=='sha256','invalid_inventory','Inventário inválido.')
    fs=RootFS(PACKAGE)
    for path,h in idx['files'].items():require(fs.hash(path)==h,'package_modified','Arquivo de pacote foi alterado.',3,path=path)
    actual={p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='integrity.json'}
    require(actual==set(idx['files']),'unexpected_package_file','Há arquivo inesperado no pacote.',3)
    return result('Bytes correspondem ao inventário. Isto não valida assinatura/autoria.',files_verified=len(actual))

def dispatch(a):
    if a.command=='verify-package':return verify_package()
    if a.command=='route':
        refs=['references/routing.md']
        if a.ux in ('UX2','UX3'):refs.append('references/ux.md')
        if a.security in ('S2','S3'):refs.append('references/security-integration.md')
        if a.operation in ('O2','O3'):refs.append('references/operations-and-release.md')
        return result('Rota baseada na classificação fornecida; reavalie o diff real.',references=refs,auditor_required=a.security in ('S2','S3'),historical_mockup_sync=False,production_authority_required=a.operation=='O3')
    if a.command=='update':
        from . import distribution as d
        return d.apply(external_data(a.plan),a.approved_digest) if a.action=='apply' else d.plan(a.archive,a.expected_sha256,a.destination,a.current_version)
    if a.command=='audit' and a.action in ('catalog','validate-request','response-template'):
        from . import audit
        if a.action=='catalog':return result('Selecione controles; isto não cria plano universal.',controls=[c for c in audit.registry()['controls'] if not a.family or c['id'].startswith('SEC-'+a.family+'-')])
        r=external_data(a.request);audit.validate_request(r)
        return audit.response_template(r) if a.action=='response-template' else result('Request estruturalmente válido; permissões declaradas não concedem autoridade.')
    require(a.root,'root_required','Informe --root para operações que leem/escrevem um projeto.')
    fs=RootFS(a.root)
    if a.command=='method':
        from . import project as pr
        if a.action=='verify':return pr.verify_adoption(fs,a.auditor_dir)
        return pr.adopt(fs,a.expected_sha256,a.authority_ref,a.auditor_dir,a.trusted_auditor_digest)
    if a.command=='doctor':
        from .project import doctor
        return doctor(fs)
    if a.command in ('init','migrate'):
        from . import migration as m
        if a.command=='init':return m.make_plan(fs,a.authority_ref,a.bootstrap_ref)
        if a.action=='inventory':return m.inventory(fs,a.paths)
        if a.action=='plan':return m.make_plan(fs,a.authority_ref,a.bootstrap_ref,resolutions=external_data(a.resolutions) if a.resolutions else None)
        if a.action=='apply':return m.apply(fs,external_data(a.plan),a.approved_digest)
        if a.action=='resume':return m.resume(fs,a.id,a.approved_digest)
        if a.action=='rollback':return m.rollback(fs,a.id,a.approved_digest)
        return m.status(fs,a.id)
    if a.command=='task':
        from .tasks import Store
        store=Store(fs)
        if a.action=='list':return result('Tasks canônicas; nenhuma escrita.',tasks=[{'path':p,'sha256':fs.hash(p),**m} for p,m,b in store.entries() if (not a.status or m['status']==a.status) and (not a.authorization or m['authorization']['status']==a.authorization)])
        if a.action=='show':
            p,m,b=store.get(a.id);return result('Task lida.',path=p,sha256=fs.hash(p),task=m,body=b)
        if a.action=='create':return store.create(external_data(a.data,yaml_ok=True),read_text(a.body_file))
        if a.action=='archive':return store.archive(a.id,a.expected_sha256)
        return store.update(a.id,external_data(a.data,yaml_ok=True) if a.data else {},a.expected_sha256,body=read_text(a.body_file) if a.body_file else None,transition=a.to if a.action=='transition' else None,authority_ref=a.authority_ref)
    if a.command in ('audit','gate'):
        from . import audit
        if a.command=='gate':return audit.gate(fs,external_data(a.request),external_data(a.response),a.operation,a.environment,a.authority_ref,a.environment_digest)
        if a.action=='snapshot':return audit.snapshot(fs,a.paths,a.environment)
        if a.action=='request':return audit.make_request(fs,a.paths,a.controls,a.surfaces,a.objective,a.impact,a.mode,a.task_id,a.orchestrator_id,a.environment,a.environment_digest,a.environment_observed)
        if a.action=='scan':return audit.scan(fs,a.paths)
        r=external_data(a.request);res=external_data(a.response)
        if a.action=='persist':return audit.persist(fs,r,res)
        audit.validate_response(r,res,fs);return result('Identidade, cobertura, evidências e snapshot validados; não é autorização de deploy.')
    if a.command=='session':
        from . import sessions as s
        if a.action=='save':return s.save(fs,a.id,a.task_id,a.paths,a.next_action,a.context,a.expected_sha256)
        return s.check(fs,a.id)
    if a.command=='host':
        raw=fs.read('AGENTS.md');require(raw is not None,'missing_agents','AGENTS.md não existe.',4)
        args=list(a.host_args)
        if args and args[0]=='--':args=args[1:]
        forbidden=('--system-prompt','--system-prompt-file','--append-system-prompt','--append-system-prompt-file','--dangerously-skip-permissions','--dangerously-bypass-approvals-and-sandbox')
        require(not any(arg.split('=')[0] in forbidden for arg in args),'unsafe_host_args','Não substitua instruções/permissões pelo wrapper.')
        command=[a.name]
        if a.name=='claude':command+=['--append-system-prompt-file',str(fs.path('AGENTS.md'))]
        command+=args
        if not a.execute:return result('Plano de inicialização; nenhum host executado.',argv=command,cwd=str(fs.root),agents_sha256=digest(raw),limitations=['Suporte de host real requer teste na versão instalada. Nenhum CLAUDE.md será criado.'])
        require(a.trust_root and a.expected_agents_sha256==digest(raw),'untrusted_bootstrap','Execução exige raiz confiada e hash esperado das instruções.',5)
        require(__import__('shutil').which(a.name),'host_unavailable','CLI do host não encontrada.',4)
        # Forward only after explicit execution/permission; built-in prompt is preserved.
        rc=subprocess.call(command,cwd=fs.root)
        require(rc==0,'host_failed','Host retornou falha.',6,returncode=rc)
        return result('Processo do host encerrado. Verifique evidências específicas da sessão.')
    raise MethodError('unknown_command','Comando não implementado.')

def main():
    try:
        args=parser().parse_args();out=dispatch(args)
        code=5 if out.get('decision')=='blocked' or out.get('status')=='needs_review' else 0
        if out.get('decision')=='blocked':out['status']='blocked';out['code']='GATE_BLOCKED'
        emit(out,getattr(args,'output',None));return code
    except MethodError as e:
        emit({'status':'error','code':e.code,'summary':e.summary,'changed_paths':[],'limitations':[],'details':e.details});return e.exit_code
    except KeyboardInterrupt:
        emit({'status':'cancelled','code':'CANCELLED','summary':'Execução interrompida; consulte journal quando houver mutação iniciada.','changed_paths':[],'limitations':[]});return 8
    except (OSError,ValueError,KeyError,TypeError) as e:
        # Do not echo raw parser errors, paths or secret-bearing input.
        emit({'status':'error','code':'RUNTIME_ERROR','summary':'Falha local. Nenhum sucesso é inferido; verifique permissões, entradas e journal.','changed_paths':[],'limitations':[],'error_type':type(e).__name__});return 7
