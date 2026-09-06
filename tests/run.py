#!/usr/bin/env python3
"""Execute local fixtures and emit an auditable test report. No model calls."""
import unittest, sys, json, platform, time, argparse, datetime
from pathlib import Path
sys.dont_write_bytecode=True
class Recorded(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.records=[]
    def addSuccess(self,test):super().addSuccess(test);self.records.append({'test':test.id(),'status':'pass'})
    def addFailure(self,test,err):super().addFailure(test,err);self.records.append({'test':test.id(),'status':'fail'})
    def addError(self,test,err):super().addError(test,err);self.records.append({'test':test.id(),'status':'error'})
    def addSkip(self,test,reason):super().addSkip(test,reason);self.records.append({'test':test.id(),'status':'skipped','reason':reason})
def main():
    p=argparse.ArgumentParser();p.add_argument('--output');a=p.parse_args()
    start=time.perf_counter();suite=unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent),pattern='test_*.py')
    out=unittest.TextTestRunner(verbosity=2,resultclass=Recorded).run(suite)
    report={'schema_version':1,'package':Path(__file__).resolve().parents[1].name,'executed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':platform.python_version(),'platform':platform.platform(),'tests_run':out.testsRun,'failures':len(out.failures),'errors':len(out.errors),'skipped':len(out.skipped),'duration_seconds':round(time.perf_counter()-start,3),'successful':out.wasSuccessful(),'tests':out.records,'model_tokens_actual':None,'host_integration':'not_run','scope':'Synthetic local runtime fixtures; not a real application audit or real Claude/Codex evaluation.'}
    raw=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if a.output:
        path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(raw,encoding='utf-8')
    else:print(raw)
    return 0 if out.wasSuccessful() else 1
if __name__=='__main__':raise SystemExit(main())
