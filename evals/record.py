#!/usr/bin/env python3
"""Record a supplied external evaluation. Does not execute or certify a model."""
import argparse,datetime,json,uuid
from pathlib import Path
p=argparse.ArgumentParser()
for n in ('case','run-id','host','model','status','evidence','output'):p.add_argument('--'+n,required=True)
p.add_argument('--input-tokens',type=int);p.add_argument('--output-tokens',type=int)
a=p.parse_args();known=json.loads((Path(__file__).parent/'scenarios.json').read_text())
if a.case not in {c['id'] for c in known['cases']}:p.error('Case desconhecido.')
if a.status not in ('pass','fail','partial','not_run'):p.error('Status inválido.')
if any(v is not None and v<0 for v in (a.input_tokens,a.output_tokens)):p.error('Tokens não podem ser negativos.')
path=Path(a.output)
if path.exists():p.error('Resultado não sobrescreve execução anterior.')
record={'record_id':str(uuid.uuid4()),'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'externally_supplied_not_independently_verified','case':a.case,'run_id':a.run_id,'host':a.host,'model':a.model,'status':a.status,'evidence_ref':a.evidence,'input_tokens_actual':a.input_tokens,'output_tokens_actual':a.output_tokens}
path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Resultado registrado, sem executar ou simular avaliação.')
