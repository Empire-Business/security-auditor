# Security Auditor — 2.0.0-rc.1

Especialista de segurança por escopo, com 31 controles em 14 famílias e evidências estruturadas.
Não é uma segunda orquestradora nem scanner que declara aplicação inteira segura.

## Uso com OMNX

A OMNX classifica o delta, prepara request 2.0 e chama o especialista disponível no host.
S0 não chama auditor por rotina. S1 usa verificação local pertinente. S2/S3 recebem revisão delimitada.
O auditor devolve cobertura, evidências e findings; OMNX integra trabalho e decisões operacionais.

## Uso independente

> Use security-auditor em modo delta para revisar este endpoint e suas dependências de autorização.
> Report-only. Não altere aplicação ou dados e não execute chamadas em produção.

Ou peça modo full explicitamente. Full ainda seleciona módulos aplicáveis, limita ferramentas e não
significa pentest ativo autorizado. Design avalia proposta, não comprova código funcionando.

## Helpers

```sh
python scripts/auditor.py audit catalog --family WEBHOOK
python scripts/auditor.py --root /caminho/projeto audit snapshot --paths src/webhook.ts
python scripts/auditor.py audit validate-request --request /tmp/request.json
python scripts/auditor.py audit response-template --request /tmp/request.json --output /tmp/template.json
python scripts/auditor.py --root /caminho/projeto audit validate-response \
  --request /tmp/request.json --response /tmp/resposta-real.json
```

**response-template retorna partial/unknown, não uma auditoria executada.** A IA executa a revisão com
as ferramentas autorizadas do host. Scripts não simulam chamada de modelo, browser, banco ou CI.
O entrypoint recusa init/migrate/task/gate/persist. Escrita de output precisa ser explicitamente pedida.

## Resultado

Pass/fail/unknown/not_applicable por controle, execução/cobertura separadas, evidência localizada,
severidade e confiança distintas de autorização de deploy. Sem score ornamental ou achado obrigatório.
Sem fonte ou teste necessário, declarar a lacuna. Não corrigir permissão/token por substituição genérica.
Não adicionar dezenas de Tasks, nem guardar backlog em relatório de auditoria.

## Organização

controls/index.json é fonte canônica do catálogo. controls/modules contém explicações carregadas sob demanda.
contracts possui request/response e política local; references detalha evidência, escopo e armadilhas técnicas.
A cópia do catálogo na OMNX é gerada, pinada e comparada, não editada como autoridade concorrente.

## Instalação

O ZIP é uma distribuição de skill, não um plugin de marketplace com conectores.
Extraia a pasta inteira, preservando SKILL.md na raiz dessa pasta. Primeiro use pasta nova ou cópia
recuperável; não sobrescreva customizações antigas sem revisar REPOSITORY-UPGRADE.md.

| Host local | Pessoal | Por projeto |
|---|---|---|
| Claude Code | `~/.claude/skills/<nome>/` | `.claude/skills/<nome>/` |
| Codex CLI | `~/.agents/skills/<nome>/` | `.agents/skills/<nome>/` |

Locais/invocação conforme documentação consultada em 6/9/2026; veja reports/SOURCES.md.
Em Claude Code use `/omnx-code` ou `/security-auditor`; em Codex CLI use `$omnx-code` ou
`$security-auditor`. Hosts corporativos, cloud e interfaces de upload podem ter mecanismo próprio.
Não confunda instruções do projeto (AGENTS.md) com a pasta de instalação da skill.

A distribuição foi testada como arquivos/scripts em Linux/Python, não dentro das CLIs reais.
Confirme descoberta/versão/escopo efetivo no seu ambiente. O instalador não modifica configuração global.

## Requisitos e verificação

As instruções funcionam com um agente capaz de ler arquivos; os helpers precisam de Python 3.10+.
Nesta entrega foram executados com Python 3.13.5/Linux. Nenhum pip, chave de API ou serviço externo é
necessário para os helpers. O modelo/assinatura do host são seus; os scripts não chamam API de LLM.

```sh
python scripts/auditor.py verify-package
python tests/run.py --output /tmp/security-auditor-test-results.json
```

`verify-package` compara bytes ao inventário, não autentica uma assinatura. O SHA-256 do ZIP deve vir
de uma origem confiada. Os arquivos não foram assinados digitalmente.
`tests/run.py` executa fixtures locais em diretórios temporários, sem testar sua aplicação/produção.

## O que está validado e o que não está

Consulte reports/VALIDATION.md e reports/test-results.json. Não há garantia de encontrar toda
vulnerabilidade nem de prever todo comportamento de um modelo. Os 130 cenários em evals/scenarios.json
são conjunto de aceitação comportamental, não 130 testes de modelo já aprovados.

Não foram executados Claude/Codex reais, homologação Windows/macOS, pentest, apps reais do usuário,
integrações Asaas/Hotmart/Supabase ou benchmark de tokens em modelo. Gates são avaliações locais,
não proteção de branch ou autorização de produção. Migração de texto precisa de resolução semântica
pelo agente/revisor: o motor não adivinha decisões de negócio.

## Atualizações e código-fonte

manifest.json identifica a versão. integrity.json é inventário gerado. Os scripts estão incluídos
em código-fonte e possuem testes. Preserve NOTICE/LICENSE e a licença de PyYAML.
Referências/históricos e exemplos não são arquivos que devam ser lidos inteiros em cada Task.

Para publicar o repositório, veja REPOSITORY-UPGRADE.md. Para distribuição versionada sem sobrescrita,
veja a referência de distribuição da OMNX. Atualização do pacote, migração documental e migração de
dados da aplicação são três operações diferentes.
