# Helpers offline do auditor

Python 3.10+, parser YAML vendorizado e schemas locais. Nenhuma instalação de pacote ou modelo é feita.
```sh
python <skill>/scripts/auditor.py audit catalog --family TENANT
python <skill>/scripts/auditor.py --root <projeto> audit snapshot --paths src/query.ts
python <skill>/scripts/auditor.py audit validate-request --request <request.json>
python <skill>/scripts/auditor.py audit response-template --request <request.json> --output <local>/response.json
python <skill>/scripts/auditor.py --root <projeto> audit validate-response --request <request.json> --response <response.json>
python <skill>/scripts/auditor.py --root <projeto> audit scan --paths src/config.ts
```
Request pode ser gerado com audit request (veja --help). Arquivos de output só quando explicitamente solicitados.
O entrypoint recusa task, migrate, init, gate e persist. Runtime compartilhado não é sandbox do Python;
limites reais de filesystem/rede pertencem ao host. Revisor continua obrigado a respeitar escopo.

Scan retorna candidatos redigidos, nunca PASS. Não faz auditoria de dependências em base de CVEs online.
Snapshot não executa código da aplicação. Response-template não é análise executada.
Somente operador/agente autorizado pode realizar testes e preencher evidência real.

Erros/limites do parser e filesystem são compartilhados com a OMNX. Não transformar falha em resultado seguro.
Siga reports/VALIDATION.md para distinguir testes locais dos helpers, evals propostos e hosts não homologados.
