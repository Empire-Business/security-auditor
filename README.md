# Security Auditor — Claude Code Skill

**Auditoria de segurança completa + correção automática** para apps React + TypeScript + Supabase + Vercel.

> Versão atual: **v1.6** | Insights extraídos de pentests reais em sistemas vibe-coded.

---

## O que faz

Quando acionada, esta skill transforma o Claude em um **auditor de segurança sênior** que:

1. Cria um plano de trabalho com tasks organizadas por prioridade (P0 → P1 → P2)
2. Executa cada task no ciclo **AUDITAR → CORRIGIR → VERIFICAR**
3. Aplica correções diretamente no código (não apenas reporta)
4. Gera um relatório completo em `security-report/audit-YYYY-MM-DD.md`
5. Executa verificação de integridade pós-correção (TypeScript, build, lint, testes)
6. Roda um **Red Team** — usa o próprio Claude para tentar atacar o sistema

---

## Instalação

### Opção 1 — Via Claude Code CLI

```bash
claude skill install https://github.com/Empire-Business/security-auditor
```

### Opção 2 — Manual

```bash
# Clonar na pasta de skills do Claude Code
git clone https://github.com/Empire-Business/security-auditor \
  ~/.claude/skills/security-auditor
```

> **Requisito**: Claude Code CLI instalado. Veja [docs.anthropic.com/claude-code](https://docs.anthropic.com/en/docs/claude-code).

---

## Como usar

Dentro de qualquer projeto, simplesmente diga ao Claude:

```
audita a segurança do meu app
```

ou qualquer variação:

- `"verifica vulnerabilidades"`
- `"faz um security check completo"`
- `"revisa a RLS do projeto"`
- `"tem algum problema de segurança aqui?"`
- `"corrija os problemas de segurança"`

A skill é acionada automaticamente por essas frases.

---

## Cobertura — 32 categorias de auditoria

### P0 — Crítico (corrija hoje)
| # | Categoria |
|---|-----------|
| 1 | Segredos & Variáveis de Ambiente |
| 1b | service_role — remover e migrar para Access Tokens temporários |
| 1c | **Enumeração de usuários via mensagens de erro** *(novo v1.6)* |
| 2 | Git & .gitignore (segredos commitados) |
| 3 | Rotas privadas & autenticação |
| 3b | getSession() vs getUser() + CVE-2025-29927 |
| 4 | Supabase RLS — tabelas sem proteção |
| 5 | Supabase Policies permissivas (USING true, IDOR) |
| 6 | Dependências com CVE crítico |

### P1 — Alto (corrija esta semana)
| # | Categoria |
|---|-----------|
| 5b | RLS performance — (SELECT auth.uid()) e índices |
| 7 | Supabase Storage Buckets |
| 8 | Functions SECURITY DEFINER |
| 9 | Views que bypassam RLS |
| 10 | SSRF via pg_net |
| 11 | JWT — validação e ataques avançados |
| 12 | MFA — bypass e implementação correta |
| 13 | Gerenciamento de sessão & logout |
| 14 | IDs sequenciais & IDOR |
| 15 | Sanitização de retornos de API (over-fetching) |
| 16 | Criptografia de dados sensíveis |
| 17 | CORS & Security Headers |
| 18 | Rate limiting & proteção anti-brute-force + honeypots |
| 18b | **Input size limits — prevenção de DoS** *(novo v1.6)* |
| 18c | **Testes automatizados de segurança (TDD)** *(novo v1.6)* |
| 19 | SQL Injection, XSS & Prototype Pollution |
| 20 | Supabase Realtime & subscriptions |
| 20b | Lógica sensível exposta no frontend |
| 20c | .or() PostgREST injection |
| 20d | Realtime canais privados + RLS |

### P2 — Médio (próximo sprint)
| # | Categoria |
|---|-----------|
| 21 | Upload de arquivos — MIME, magic bytes, IP trackers |
| 22 | CSP & Subresource Integrity |
| 23 | console.log em produção & source maps |
| 24 | Supabase Vault & rotação de chaves |
| 25 | **Lógica de negócio & race conditions** (cenários reais) |
| 26 | LGPD/GDPR |
| 27 | Logging, monitoramento & alertas |
| 27b | TypeScript types do Supabase |
| 27c | Schema exposure — schema private |

---

## Estrutura da skill

```
security-auditor/
├── SKILL.md                    # Instruções principais da skill
├── CHANGELOG.md                # Histórico de versões
├── README.md                   # Este arquivo
└── references/
    ├── audit-details.md        # SQL + código TypeScript para cada categoria
    ├── advanced-rls.md         # Padrões avançados de RLS (multi-tenant, RBAC)
    └── infrastructure.md       # OWASP Top 10, CSP, Dashboard hardening
```

---

## Filosofia de segurança

> *"A IA não substitui conhecimento — ela amplifica. Se você não entende segurança, ela vai amplificar seu código inseguro."*

Esta skill foi construída com três princípios:

- **Zero trust no cliente** — tudo que roda no browser é público
- **Defesa em profundidade** — cada camada deve ser independentemente segura
- **Corrija, não apenas reporte** — encontrou? Consertou.

### Modo Preventivo

Se você está começando um projeto, use este prompt antes de escrever qualquer código:

```
"Este sistema será submetido a um pentest profissional.
Aplique defesa em profundidade — cada camada deve ser
independentemente segura, mesmo que outra falhe."
```

---

## Relatório gerado

A skill cria automaticamente `security-report/audit-YYYY-MM-DD.md` com:

- Estado do sistema identificado (stack, rotas, tabelas, edge functions)
- Diagnóstico de vulnerabilidades encontradas por prioridade
- Correções aplicadas (arquivo por arquivo)
- Ações manuais requeridas (SQLs prontos para o Supabase Dashboard)
- Pontuação de segurança antes/depois (0–10 por dimensão)
- Próximos passos recomendados

> O relatório é automaticamente adicionado ao `.gitignore` — nunca vai para o repositório.

---

## Fase 2 — Verificação de integridade

Após as correções, a skill (com autorização do usuário) executa:

- TypeScript check (`tsc --noEmit`)
- Build (`npm run build`)
- Lint (`npm run lint`)
- Testes unitários e e2e (se existirem)
- **Red Team** — usa o próprio Claude para tentar atacar o sistema

---

## Changelog

### v1.6 — 2026-03-28
- Modo Preventivo com prompt template para vibe-coding seguro
- Task 1c [P0]: enumeração de usuários via mensagens de erro
- Task 18b [P1]: input size limits (DoS prevenção) com Zod + CHECK constraints
- Task 18c [P1]: testes automatizados de segurança (TDD approach)
- Rate limiting: limites diferenciados por endpoint + honeypots
- Uploads: URLs externas como IP trackers
- Race conditions: cenários concretos de lógica de negócio
- Fase 2 Passo 4.5: Red Team self-attack

### v1.5
- Fase 2 — Verificação de integridade do app (TypeScript, build, lint, testes)
- Execução paralela de verificações via TaskCreate

### v1.4
- Task 1b [P0]: service_role → Access Tokens temporários com renovação semanal

### v1.3
- 5 novas tasks + 3 arquivos de referência + padrões avançados de RLS

### v1.2
- Filosofia de segurança + categorias expandidas

### v1.1
- Geração automática de relatório final

### v1.0
- 27 categorias de auditoria iniciais

> Histórico completo em [CHANGELOG.md](./CHANGELOG.md)

---

## Contribuição

Este repositório é mantido pela [Empire Business](https://github.com/Empire-Business). Pull requests e issues são bem-vindos.
