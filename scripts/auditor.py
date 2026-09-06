#!/usr/bin/env python3
"""Read-only specialist entrypoint; output writes only when explicitly requested."""
import sys
sys.dont_write_bytecode = True
from omnxlib.cli import parser, dispatch
from omnxlib.core import emit, MethodError

def main():
    try:
        import argparse
        p=parser()
        main_sub=next(a for a in p._actions if isinstance(a,argparse._SubParsersAction))
        for name in list(main_sub.choices):
            if name not in ('audit','verify-package'):del main_sub.choices[name]
        audit_sub=next(a for a in main_sub.choices['audit']._actions if isinstance(a,argparse._SubParsersAction))
        del audit_sub.choices['persist']
        args=p.parse_args()
        allowed=(args.command=='verify-package' or (args.command=='audit' and args.action!='persist'))
        if not allowed:
            raise MethodError('specialist_read_only','Use a OMNX para tarefas, migração e persistência canônica. O especialista apenas revisa.',5)
        emit(dispatch(args),getattr(args,'output',None))
        return 0
    except MethodError as e:
        emit({'status':'error','code':e.code,'summary':e.summary,'changed_paths':[],'limitations':[]});return e.exit_code
    except KeyboardInterrupt:
        emit({'status':'cancelled','code':'CANCELLED','summary':'Revisão interrompida. Nenhum PASS implícito.','changed_paths':[],'limitations':[]});return 8
    except (OSError,ValueError,KeyError,TypeError) as e:
        emit({'status':'error','code':'RUNTIME_ERROR','summary':'Falha no helper; não implica auditoria concluída.','changed_paths':[],'limitations':[],'error_type':type(e).__name__});return 7
if __name__=='__main__':
    raise SystemExit(main())
