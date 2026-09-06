import sys
from pathlib import Path
PACKAGE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PACKAGE/'scripts'))
sys.dont_write_bytecode=True
"""Deterministic tests with synthetic local fixtures; no real host/application audit."""

import unittest

import tempfile

import subprocess

import os

import sys

import json

import copy

import threading

import time

import zipfile

import io

from pathlib import Path

PACKAGE=Path(__file__).resolve().parents[1]

sys.dont_write_bytecode=True

from omnxlib.core import *

from omnxlib import migration as mg, project as pr, tasks as ts, audit as au, distribution as dist, sessions

class Base(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.fs=RootFS(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def init(self):
        p=mg.make_plan(self.fs,'user:test-adoption','explicit-skill:canonical-read');mg.apply(self.fs,p,p['plan_digest']);return p
    def task(self,status='ready'):
        return ts.Store(self.fs).create({'title':'Objetivo sintético','status':status,'authorization':{'status':'authorized' if status=='ready' else 'proposed','basis_ref':'user:synthetic-scope' if status=='ready' else None},'acceptance':['Resultado esperado verificável.']},'Somente fixture local. Não publicar.')
    def expect(self,code,fn):
        with self.assertRaises(MethodError) as c:fn()
        self.assertEqual(c.exception.code,code)
    def files(self):return {p.relative_to(self.fs.root).as_posix():p.read_bytes() for p in self.fs.root.rglob('*') if p.is_file()}
    def legacy(self):
        self.fs.write('CLAUDE.md',b'# Local rule\r\nNever deploy automatically.\r\n',None)
        self.fs.write('AGENTS.md',b'# Existing rule\nKeep user data.\n',None)
        self.fs.write('src/app.py',b'untouched = True\n',None)
        paths=['CLAUDE.md','AGENTS.md'];mappings=[]
        combined=pr.AGENTS.encode()+b'\n'
        for path in paths:
            raw=self.fs.read(path);combined+=raw+b'\n'
            for b in mg.blocks(raw):
                mappings.append({'source_path':path,'block_id':b['id'],'block_sha256':b['sha256'],'category':'instruction','treatment':'preserve','destination':'AGENTS.md','reason':'Preservar regra operacional customizada.','decision_ref':None})
        resolutions={'source_paths':paths,'mappings':mappings,'writes':{'AGENTS.md':combined.decode()}}
        return mg.make_plan(self.fs,'user:legacy-migration','explicit-skill:AGENTS-reviewed',resolutions=resolutions)
    def request(self,controls=None):
        if self.fs.read('src/input.py') is None:self.fs.write('src/input.py',b'def handle(x): return x\n',None)
        return au.make_request(self.fs,['src/input.py'],controls or ['SEC-INPUT-01'],['input'],'Revisão sintética local')
    def passed(self,r):
        a=au.response_template(r)
        a['execution_status']='completed';a['surface_discovery_status']='completed';a['unassessed_surfaces']=[];a['limitations']=[]
        for i,row in enumerate(a['control_results']):
            eid='EV-test-'+str(i)
            row.update(assessment='evaluated',result='pass',evidence_ids=[eid],rationale='Evidência sintética do teste deste runtime.',limitation_code=None)
            a['evidence'].append({'id':eid,'kind':'test','reference':'test-runtime:synthetic-test','result':'pass','environment':'local','observed_at':now(),'summary':'Fixture sintética local; não auditoria real.'})
        return a

class ParserAndFilesystem(Base):
    def test_json_duplicate(self):self.expect('duplicate_key',lambda:load_data('{"role":1,"role":2}'))
    def test_yaml_duplicate(self):self.expect('duplicate_key',lambda:load_data('role: one\nrole: two',yaml_ok=True))
    def test_yaml_alias(self):self.expect('yaml_alias',lambda:load_data('a: &x [1]\nb: *x',yaml_ok=True))
    def test_yaml_executable_tag(self):self.expect('invalid_document',lambda:load_data('!!python/object/apply:os.system ["touch nope"]',yaml_ok=True))
    def test_json_nonfinite(self):self.expect('invalid_number',lambda:load_data('{"x":NaN}'))
    def test_timestamp_without_zone(self):self.expect('invalid_time',lambda:timestamp('2026-09-06T12:00:00'))
    def test_yaml_timestamp_stays_string(self):self.assertIsInstance(load_data('date: 2026-09-06',yaml_ok=True)['date'],str)
    def test_size_limit(self):self.expect('document_limit',lambda:load_data(b' '* (MAX_DOCUMENT+1)))
    def test_deep_yaml(self):self.expect('document_limit',lambda:load_data('['*60+'0'+']'*60,yaml_ok=True))
    def test_duplicate_non_string_yaml(self):self.expect('invalid_key',lambda:load_data('1: value',yaml_ok=True))
    def test_path_traversal(self):self.expect('invalid_path',lambda:self.fs.write('../escape',b'x',None))
    def test_absolute_path(self):self.expect('invalid_path',lambda:self.fs.read('/etc/passwd'))
    def test_windows_device(self):self.expect('invalid_path',lambda:portable_path('docs/CON.md'))
    def test_unicode_normalization(self):self.expect('invalid_path',lambda:portable_path('docs/cafe\u0301.md'))
    def test_symlink_rejected(self):
        outside=Path(self.tmp.name).parent/'not-written-by-test'
        (self.fs.root/'link').symlink_to(outside);self.expect('unsafe_link',lambda:self.fs.read('link'))
    def test_hardlink_rejected(self):
        self.fs.write('original',b'x',None);os.link(self.fs.root/'original',self.fs.root/'linked');self.expect('unsafe_link',lambda:self.fs.read('linked'))
    def test_file_obstructs_directory(self):
        self.fs.write('docs',b'x',None);self.expect('path_conflict',lambda:self.fs.write('docs/PRD.md',b'x',None))
    def test_cas(self):
        self.fs.write('file',b'one',None);self.expect('stale_state',lambda:self.fs.write('file',b'two',digest(b'other')));self.assertEqual(self.fs.read('file'),b'one')
    def test_lock_contention(self):
        with metadata_lock(self.fs):self.expect('locked',lambda:self._lock_once())
    def _lock_once(self):
        with metadata_lock(self.fs):pass
    def test_lock_released(self):
        with metadata_lock(self.fs):pass
        self._lock_once()
    def test_unknown_schema_keyword(self):self.expect('unsupported_schema',lambda:validate({}, {'unevaluatedProperties':False}))
    def test_schema_bool_not_int(self):self.expect('schema_validation',lambda:validate(True,{'type':'integer'}))

class AuditTests(Base):
    def test_template_not_pass(self):
        r=self.request();a=au.response_template(r);au.validate_response(r,a,self.fs);self.assertEqual(a['execution_status'],'partial');self.assertTrue(all(x['result']=='unknown' for x in a['control_results']))
    def test_missing_control(self):
        r=self.request();a=au.response_template(r);a['control_results']=[];self.expect('missing_control',lambda:au.validate_response(r,a))
    def test_duplicate_control(self):
        r=self.request();a=au.response_template(r);a['control_results']*=2;self.expect('duplicate_control',lambda:au.validate_response(r,a))
    def test_unknown_enum(self):
        r=self.request();a=au.response_template(r);a['control_results'][0]['result']='sort_of_safe';self.expect('schema_validation',lambda:au.validate_response(r,a))
    def test_missing_evidence_for_pass(self):
        r=self.request();a=au.response_template(r);a['control_results'][0].update(result='pass',assessment='evaluated');self.expect('unsupported_conclusion',lambda:au.validate_response(r,a))
    def test_different_snapshot(self):
        r=self.request();a=au.response_template(r);a['snapshot_content_digest']='f'*64;self.expect('snapshot_mismatch',lambda:au.validate_response(r,a))
    def test_dirty_file_invalidates(self):
        r=self.request();a=self.passed(r);self.fs.write('src/input.py',b'changed\n',self.fs.hash('src/input.py'));self.expect('stale_evidence',lambda:au.validate_response(r,a,self.fs))
    def test_unrelated_file_does_not_invalidate(self):
        r=self.request();a=self.passed(r);self.fs.write('other.txt',b'changed',None);au.validate_response(r,a,self.fs)
    def test_environment_digest_tampering(self):
        r=self.request();r['snapshot']['environment_config_digest']='a'*64;self.expect('snapshot_digest',lambda:au.validate_request(r))
    def test_completed_unknown_not_gate_pass(self):
        r=self.request();a=au.response_template(r);a.update(execution_status='completed',surface_discovery_status='completed',unassessed_surfaces=[]);a['control_results'][0]['assessment']='evaluated';au.validate_response(r,a);self.assertEqual(au.gate(self.fs,r,a,'merge','local')['decision'],'blocked')
    def test_design_not_implementation(self):
        r=self.request();r['mode']='design';a=self.passed(r);self.assertIn('DESIGN_IS_NOT_IMPLEMENTATION',au.gate(self.fs,r,a,'merge','local')['reasons'])
    def test_tenant_pass_requires_behavior(self):
        r=self.request(['SEC-TENANT-01']);a=self.passed(r);a['evidence'][0]['kind']='static';self.expect('behavior_not_verified',lambda:au.validate_response(r,a))
    def test_no_automatic_production(self):
        r=self.request();a=self.passed(r);self.assertIn('DEPLOY_AUTHORITY_REQUIRED',au.gate(self.fs,r,a,'deploy','local')['reasons'])
    def test_valid_local_merge(self):
        r=self.request();a=self.passed(r);self.assertEqual(au.gate(self.fs,r,a,'merge','local')['decision'],'allowed')
    def test_policy_modified_rejected(self):
        r=self.request();r['policy_digest']='f'*64;self.expect('policy_mismatch',lambda:au.validate_request(r))
    def test_registry_modified_rejected(self):
        r=self.request();r['control_registry_digest']='f'*64;self.expect('registry_mismatch',lambda:au.validate_request(r))
    def test_false_completion(self):
        r=self.request();a=au.response_template(r);a['execution_status']='completed';self.expect('false_completion',lambda:au.validate_response(r,a))
    def test_synthetic_example_field_rejected(self):
        r=self.request();a=self.passed(r);a['evidence'][0]['synthetic_example']=True;self.expect('schema_validation',lambda:au.validate_response(r,a))
    def test_secret_path_not_snapshotted(self):
        self.fs.write('.env',b'not-a-real-secret',None);self.expect('secret_path',lambda:au.snapshot(self.fs,['.env']))
    def test_scan_redacts_before_output(self):
        fake=b'sb_secret_' + b'SYNTHETIC_TEST_VALUE_000'
        self.fs.write('source.txt',fake,None);out=au.scan(self.fs,['source.txt']);self.assertTrue(out['candidates']);self.assertNotIn(fake.decode(),json.dumps(out))
    def test_public_key_not_automatic_secret(self):
        self.fs.write('source.txt',b'sb_publishable_SYNTHETIC_TEST_VALUE_000',None);self.assertFalse(au.scan(self.fs,['source.txt'])['candidates'])
    def test_receipt_idempotency(self):
        self.init();r=self.request();a=self.passed(r);au.persist(self.fs,r,a);second=au.persist(self.fs,r,a);self.assertEqual(second['changed_paths'],[])
    def test_receipt_immutable(self):
        self.init();r=self.request();a=self.passed(r);au.persist(self.fs,r,a);a['metrics']['tool_calls']=12;self.expect('receipt_conflict',lambda:au.persist(self.fs,r,a))
    def test_local_commit_not_universal_gate(self):
        r=self.request();a=au.response_template(r);self.assertEqual(au.gate(self.fs,r,a,'commit','local')['decision'],'allowed')
    def test_new_file_is_manifested(self):
        r=self.request();self.assertIsNotNone(r['snapshot']['files'][0]['sha256'])
    def test_git_index_change_invalidates(self):
        subprocess.run(['git','init','-q',str(self.fs.root)],check=True);r=self.request();a=self.passed(r);subprocess.run(['git','-C',str(self.fs.root),'add','src/input.py'],check=True);self.expect('stale_evidence',lambda:au.validate_response(r,a,self.fs))

if __name__=="__main__": unittest.main(verbosity=2)
