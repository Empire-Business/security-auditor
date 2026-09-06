# Preservação e correção do legado

| Capacidade observada/solicitada | Destino novo | Tratamento |
|---|---|---|
| Orientação de produto e implementação | OMNX núcleo + routing | Mantida, proporcional ao pedido |
| Brief/PRD/arquitetura | information-model + templates | Separada de execução/disponibilidade |
| Mockup-first | ux | Redução de incerteza, sem sincronização eterna |
| Dona Maria e guardião | ux | Inspeção delimitada, sem achado obrigatório |
| Tasks do agente | Task Store + CLI | Uma fonte, autorização separada, CAS |
| Handoff | checkpoint por sessão/worktree | Não é backlog nem latest global |
| CLAUDE/AGENTS equivalentes | AGENTS + adaptadores | Equivalência eliminada; host real não homologado |
| Update fixado em tag antiga | distribuição offline por digest | Downgrade recusado, pasta versionada nova |
| Migração .empire/state e docs misturados | resolução semântica + journal | Governança explícita, backup inerte e rollback |
| Auditoria universal/task por categoria | protocolo delta/design/full | Eliminada como padrão; catálogo sob demanda |
| Report-only e conteúdo injetado | auditor núcleo + LLM/SUPPLY | Mantidos e reforçados |
| Evidências/veredito | schemas e recibos | Execução, cobertura, resultado e operação separados |
| Auth/RLS/claims | AUTHN/AUTHZ/TENANT | Verificação do fluxo, sem copiar SQL contraditório |
| Segredos e tokens | SECRET | Função correta; PAT não substitui Data API genericamente |
| Webhooks/efeitos financeiros | WEBHOOK/PAY | Protocolo real, concorrência, conta e ordem |
| Injeção/browser/arquivos/rede | INPUT/OUTPUT/FILE/NET | Módulos focados, não receitas universais |
| Dados/privacidade/observabilidade | DATA/OPS/OUTPUT | Salvaguardas e limites, não certificação jurídica |
| Dependências/CI/agentes/RAG | SUPPLY/LLM | Escopo, autoridade, origem e isolamento |
| Pentest/red team | full quando autorizado | Sem pentest automático; execução ativa não incluída |
| Loja de Apps/suporte próprios | decisão de produto | Opcionais em novos projetos; não removidos dos antigos |
| Reset remoto como fallback | operations/data | Expressamente proibido como fallback automático |

A matriz é de capacidades e referências inspecionadas, não uma afirmação de auditoria de cada arquivo
ou preservação literal de todo o repositório antigo. Conteúdo sem equivalência demonstrada precisa
revisão na adoção; não importar o núcleo antigo inteiro por receio de perder um ritual.
