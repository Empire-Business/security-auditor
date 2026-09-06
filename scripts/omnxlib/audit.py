"""Audit contracts and evidence helpers, NOT an automatic security certification."""
from __future__ import annotations
from .core import *
from .project import git

TEST_CONTROLS={'SEC-TENANT-01','SEC-AUTHZ-01','SEC-WEBHOOK-02'}

def registry():
    p=PACKAGE/'controls/index.json'
    if not p.exists():p=PACKAGE/'contracts/control-index.json'
    data=load_data(p.read_bytes())
    require(data['revision']==1,'registry_version','Catálogo incompatível.',4)
    return data

def policy():return load_data((PACKAGE/'contracts/default-policy.json').read_bytes())

def safe_evidence_path(path):
    portable_path(path)
    name=path.rsplit('/',1)[-1].lower()
    require(not (name=='.env' or (name.startswith('.env.') and not name.endswith(('.example','.sample'))) or name.endswith(('.pem','.key','.p12','.pfx')) or name in ('credentials','id_rsa','id_ed25519')),'secret_path','Use referências opacas para segredos; não gere manifesto/conteúdo de credencial.')
    require(not any(p in ('.git','node_modules','.venv') for p in path.split('/')),'evidence_scope','Dependência/diretório interno não pertence à leitura direta deste helper.')
    return path

def snapshot(fs,paths,environment='local',environment_digest=None,environment_observed=False,base_revision=None):
    require(paths and len(paths)<=1000 and len(paths)==len(set(paths)),'snapshot_paths','Manifesto exige paths explícitos e únicos (máximo 1000).')
    files=[]
    for path in sorted(paths):
        safe_evidence_path(path)
        indexed=git(fs,['ls-files','--stage','--',path]);blob=None
        if indexed:
            rows=indexed.splitlines();require(len(rows)==1,'unmerged_index','Índice Git em conflito no escopo auditado.',3)
            fields=rows[0].split(None,3);require(len(fields)==4 and fields[2]=='0','unmerged_index','Resolva conflito staged antes de snapshot.',3);blob=fields[1]
        files.append({'path':path,'sha256':fs.hash(path),'git_index_blob':blob})
    # Exclude HEAD from the content identity so an unrelated commit need not invalidate it.
    d=object_digest({'files':files,'environment':environment,'environment_observed':environment_observed,'environment_config_digest':environment_digest})
    return {'kind':'git_worktree' if git(fs,['rev-parse','--show-toplevel']) else 'filesystem','base_revision':base_revision,'head_revision':git(fs,['rev-parse','HEAD']),'content_digest':d,'files':files,'environment':environment,'environment_observed':environment_observed,'environment_config_digest':environment_digest}

def validate_request(r):
    validate(r,schema('audit-request','contracts'))
    require((r['task_id'] is None)==(r['orchestrator_id'] is None),'delegation_identity','Task e orquestrador devem existir juntos ou ser null no standalone.')
    known={c['id'] for c in registry()['controls']}
    require(set(r['requested_controls'])<=known,'unknown_control','Controle não existe no catálogo adotado.',4)
    require(r['control_registry_digest']==object_digest(registry()),'registry_mismatch','Digest de catálogo incompatível.',4)
    require(r['policy_digest']==object_digest(policy()),'policy_mismatch','Este runtime valida a política local distribuída; política diferente exige adaptador confiável.',4)
    if r['mode']=='delta':require(r['requested_controls'] and r['surfaces'],'empty_delta','Delta precisa de controles e superfícies explícitos.')
    snap=r['snapshot'];paths=[x['path'] for x in snap['files']]
    require(len(paths)==len(set(paths)),'duplicate_path','Path duplicado no manifesto.')
    for path in paths:safe_evidence_path(path)
    require(set(r['changed_paths'])<=set(paths),'missing_changed_file','Arquivo alterado não está no snapshot.')
    require(snap['content_digest']==object_digest({'files':snap['files'],'environment':snap['environment'],'environment_observed':snap['environment_observed'],'environment_config_digest':snap['environment_config_digest']}),'snapshot_digest','Digest do manifesto não corresponde.')
    require(r['permissions']['network_access'] or not r['permissions']['allowed_network_targets'],'permission_mismatch','Destinos de rede não concedem acesso quando network_access=false.')
    return r

def make_request(fs,paths,controls,surfaces,objective,impact='S2',mode='delta',task_id=None,orchestrator_id=None,environment='local',environment_digest=None,environment_observed=False):
    conf=fs.data('.omnx/project.yaml',yaml_ok=True)
    pid=conf['project_id'] if conf else str(uuid.uuid5(uuid.NAMESPACE_URL,str(fs.root)))
    r={'contract_version':'2.0','request_id':new_id('ARQ'),'project_id':pid,'task_id':task_id,'orchestrator_id':orchestrator_id,'mode':mode,'objective':objective,'security_impact':impact,'snapshot':snapshot(fs,paths,environment,environment_digest,environment_observed),'policy_digest':object_digest(policy()),'control_registry_digest':object_digest(registry()),'changed_paths':paths,'surfaces':surfaces,'requested_controls':controls,'evidence_refs':[],'permissions':{'application_writes':False,'network_access':False,'allowed_network_targets':[],'sandbox_test_execution':False,'production_access':False},'budget':{'max_related_files':30,'max_tool_calls':30,'max_output_tokens':2500,'max_correction_cycles':2},'expansion_policy':'related_dependencies_with_reason'}
    validate_request(r);return r

def response_template(r):
    validate_request(r)
    return {'contract_version':'2.0','request_id':r['request_id'],'audit_id':new_id('AUD'),'project_id':r['project_id'],'task_id':r['task_id'],'mode':r['mode'],'execution_status':'partial','review_kind':'self_review','snapshot_content_digest':r['snapshot']['content_digest'],'policy_digest':r['policy_digest'],'control_registry_digest':r['control_registry_digest'],'surface_discovery_status':'not_started','unassessed_surfaces':r['surfaces'],'control_results':[{'control_id':c,'origin':'requested','assessment':'deferred','result':'unknown','evidence_ids':[],'rationale':'Revisão ainda não executada.','limitation_code':'NOT_RUN'} for c in r['requested_controls']],'findings':[],'evidence':[],'out_of_scope_observations':[],'limitations':[{'code':'NOT_RUN','summary':'Este é um molde, não uma auditoria executada.'}],'metrics':{'tool_calls':None,'tokens_actual':None,'tokens_estimated':None}}

def validate_response(r,a,fs=None):
    validate_request(r);validate(a,schema('audit-response','contracts'))
    for k in ('contract_version','request_id','project_id','task_id','mode','policy_digest','control_registry_digest'):
        require(r[k]==a[k],'response_identity','Resposta não corresponde ao request/contrato/política.',3)
    require(a['snapshot_content_digest']==r['snapshot']['content_digest'],'snapshot_mismatch','Resposta analisou outro conteúdo.',3)
    if fs:
        s=r['snapshot'];current=snapshot(fs,[x['path'] for x in s['files']],s['environment'],s['environment_config_digest'],s['environment_observed'])
        require(current['content_digest']==s['content_digest'],'stale_evidence','Conteúdo ou índice mudou desde o snapshot.',3)
        conf=fs.data('.omnx/project.yaml',yaml_ok=True)
        if conf:require(conf['project_id']==r['project_id'],'wrong_project','Evidência pertence a outro projeto.',3)
    rows=a['control_results'];row_ids=[x['control_id'] for x in rows]
    require(len(row_ids)==len(set(row_ids)),'duplicate_control','Controle duplicado no resultado.')
    require(set(r['requested_controls'])<=set(row_ids),'missing_control','Controle solicitado foi omitido; registre unknown/deferred explicitamente.')
    known={c['id'] for c in registry()['controls']}
    require(set(row_ids)<=known,'unknown_control','Resultado usa controle inexistente no catálogo.',4)
    evidence={e['id']:e for e in a['evidence']}
    require(len(evidence)==len(a['evidence']),'duplicate_evidence','Evidência com ID duplicado.')
    snap_paths={x['path']:x['sha256'] for x in r['snapshot']['files']}
    for e in a['evidence']:
        t=timestamp(e['observed_at']);require(t<=dt.datetime.now(dt.timezone.utc)+dt.timedelta(minutes=5),'future_evidence','Evidência declara observação futura.')
        if e.get('path'):
            require(e['path'] in snap_paths and e.get('file_sha256')==snap_paths[e['path']],'evidence_file_mismatch','Evidência aponta a arquivo/hash fora do snapshot.')
        if e['reference'].startswith('fixture://'):raise MethodError('synthetic_evidence','Fixture ilustrativa não é evidência operacional.',5)
    for row in rows:
        expected_origin='requested' if row['control_id'] in r['requested_controls'] else 'added'
        require(row['origin']==expected_origin,'control_origin','Origem do controle incorreta.')
        require(set(row['evidence_ids'])<=set(evidence),'missing_evidence','Referência de evidência inexistente.')
        if row['assessment']!='evaluated':require(row['result']=='unknown' and row['limitation_code'],'unassessed_pass','Controle não avaliado só pode ser unknown com motivo.')
        if row['result'] in ('pass','fail'):
            require(row['assessment']=='evaluated' and row['evidence_ids'],'unsupported_conclusion','Pass/fail exigem avaliação e evidência.')
            usable=[evidence[k] for k in row['evidence_ids'] if evidence[k]['result']!='not_run']
            require(usable,'unexecuted_evidence','Evidência não executada não sustenta conclusão.')
            if row['result']=='pass':
                require(not any(e['result']=='fail' for e in usable),'contradictory_pass','Evidência de falha contradiz PASS.')
                if r['mode']!='design' and row['control_id'] in TEST_CONTROLS:
                    require(any(e['kind']=='test' and e['result']=='pass' for e in usable),'behavior_not_verified','Este controle exige evidência comportamental pertinente; use unknown se não executou.',5)
    finding_ids=[f['id'] for f in a['findings']]
    require(len(set(finding_ids))==len(finding_ids),'duplicate_finding','Finding duplicado.')
    for f in a['findings']:
        require(f['control_id'] in row_ids and set(f['evidence_ids'])<=set(evidence),'invalid_finding','Finding sem controle/evidência correspondente.')
        row=next(x for x in rows if x['control_id']==f['control_id'])
        require(row['result'] in ('fail','unknown'),'contradictory_finding','Finding deve corresponder a falha ou hipótese inconclusiva.')
    if a['execution_status']=='completed':
        require(a['surface_discovery_status']=='completed' and not a['unassessed_surfaces'] and all(x['assessment']!='deferred' for x in rows),'false_completion','Cobertura adiada não pode ser declarada execução completa.')
    return a

def persist(fs,r,a):
    from .project import ensure_writable
    ensure_writable(fs);validate_response(r,a,fs)
    path='.omnx/security/runs/'+a['audit_id']+'.json'
    raw=json_bytes({'schema_version':1,'request':r,'response':a})
    with metadata_lock(fs):
        existing=fs.read(path)
        require(existing is None or existing==raw,'receipt_conflict','Recibo imutável já existe com outro conteúdo.',3)
        if existing is None:fs.write(path,raw,None)
    return result('Recibo preservado; não autoriza deploy e não prova autoria independente.',changed_paths=[] if existing else [path],receipt_ref=path)

def gate(fs,r,a,operation,environment,authority_ref=None,environment_digest=None):
    require(operation in ('local_edit','commit','merge','deploy'),'invalid_operation','Operação desconhecida.')
    if operation in ('local_edit','commit'):
        return result('Nenhuma auditoria universal exigida para trabalho local autorizado.',decision='allowed',enforcement='local_assessment',limitations=['Permissões do host, segredos e escopo continuam obrigatórios.'])
    validate_response(r,a,fs)
    reasons=[]
    if r['task_id'] is not None:
        from .tasks import Store
        _,task,_=Store(fs).get(r['task_id'])
        if task['authorization']['status']!='authorized' or task['status']=='cancelled':reasons.append('TASK_NOT_AUTHORIZED')
    if r['security_impact'] in ('S2','S3') and not a['control_results']:reasons.append('EMPTY_CONTROL_COVERAGE')
    if r['mode']=='design':reasons.append('DESIGN_IS_NOT_IMPLEMENTATION')
    if a['execution_status']!='completed' or a['surface_discovery_status']!='completed':reasons.append('INCOMPLETE_COVERAGE')
    for row in a['control_results']:
        if row['control_id'] in r['requested_controls'] and row['result'] in ('unknown','fail'):reasons.append('REQUIRED_CONTROL_'+row['result'].upper()+':'+row['control_id'])
    for f in a['findings']:
        if f['severity'] in ('critical','high') and f['exposure'] in ('in_scope','known_exposed'):reasons.append('EXPOSED_HIGH_RISK:'+f['id'])
        if operation=='deploy' and f['severity']=='critical' and f['exposure']=='out_of_scope_unknown':reasons.append('CRITICAL_EXPOSURE_UNRESOLVED:'+f['id'])
    if a['evidence']:
        oldest=min(timestamp(e['observed_at']) for e in a['evidence'])
        if dt.datetime.now(dt.timezone.utc)-oldest>dt.timedelta(hours=policy()['max_receipt_age_hours']):reasons.append('EVIDENCE_EXPIRED_REVIEW_NEEDED')
    if operation=='deploy':
        if not authority_ref:reasons.append('DEPLOY_AUTHORITY_REQUIRED')
        s=r['snapshot']
        if environment!=s['environment']:reasons.append('ENVIRONMENT_NOT_REVIEWED')
        if r['security_impact']=='S3' and (not s['environment_observed'] or not environment_digest or environment_digest!=s['environment_config_digest']):reasons.append('ENVIRONMENT_EVIDENCE_REQUIRED')
    decision='blocked' if reasons else 'allowed'
    return result('Operação bloqueada por evidência/autoridade específica.' if reasons else 'Critérios locais satisfeitos no escopo avaliado.',decision=decision,reasons=reasons,operation=operation,environment=environment,enforcement='local_assessment',allowed_work=['Diagnóstico e edição local autorizados continuam possíveis.'],limitations=['Não instala branch protection, não comprova autoridade humana pela string e não executa publicação. Hash não é assinatura; drift externo exige observação confiável.'])

def scan(fs,paths):
    # Candidate discovery only; values never enter output, no network calls.
    rules=[('private_key',re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')),
           ('privileged_supabase_key',re.compile(rb'sb_secret_[A-Za-z0-9_-]{12,}')),
           ('credential_assignment',re.compile(rb'(?i)(?:api_secret|access_token|password|private_key)\s*[:=]\s*[\x22\x27]([^\x22\x27\r\n]{12,})'))]
    candidates=[]
    for path in paths:
        safe_evidence_path(path);raw=fs.read(path)
        if raw is None:continue
        for rule,rx in rules:
            for m in rx.finditer(raw):
                candidates.append({'path':path,'line':raw.count(b'\n',0,m.start())+1,'rule':rule,'value':'[REDACTED]','classification':'candidate_not_confirmed'})
    return result('Varredura local de candidatos; não certifica ausência de segredos.',candidates=candidates,limitations=['Padrões limitados; chaves publicáveis não são tratadas automaticamente como segredo. Revise natureza e exposição sem copiar valores.'])
