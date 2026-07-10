# Security Auditor — Claude Code Skill

**Auditoria de segurança + correção assistida** para apps React + TypeScript + Supabase + Vercel/Next.js **web**.

> Versão atual: **v1.9** | Verificação real (re-teste + re-query no banco + scanners), threat model antes do checklist, cobertura ampliada (IA/LLM, Edge/Deno, ORM, OAuth/OIDC, lógica de borda), Guardrails v2 (anti-prompt-injection, auto-update assinado, auto-fix opt-in).
>
> **Escopo e limites:** audita a stack web React/Next.js + Supabase + Vercel. **Não** cobre internals de IA/LLM, mobile/Expo/RN, ORMs com conexão direta fora do supabase-js, posture de CI/CD, nem certifica PCI-DSS/HIPAA/SOC2. O relatório declara essas exclusões. Auditoria de IA não substitui revisão por profissional de segurança.

---

## O que faz

Quando acionada, esta skill transforma o Claude em um **auditor de segurança sênior** que:

1. Cria um plano de trabalho com tasks organizadas por prioridade (P0 → P1 → P2)
2. Executa cada task no ciclo **AUDITAR → PROPOR → (CORRIGIR só com confirmação) → VERIFICAR**
3. **Report-only por padrão**: propõe correções e aplica (Edit/Write/SQL) somente após confirmação explícita do usuário, por mudança de risco
4. Gera um relatório em `security-report/audit-YYYY-MM-DD.md` **e** um veredito machine-readable em `security-report/verdict.json` (contrato que a `omnx-code` lê para o gate de deploy)
5. Executa verificação de integridade pós-correção (TypeScript, build, lint, testes)
6. Roda um **Red Team** — usa o próprio Claude para tentar atacar o sistema

---

## Instalação

### Opção 1 — Via Claude Code CLI

```bash
claude skill install https://github.com/Empire-Business/security-auditor
```

### Opção 2 — Manual (Claude Code)

```bash
git clone https://github.com/Empire-Business/security-auditor \
  ~/.claude/skills/security-auditor
```

> **Requisito**: Claude Code CLI instalado. Veja [docs.anthropic.com/claude-code](https://docs.anthropic.com/en/docs/claude-code).

### Opção 3 — OpenAI Codex

```bash
git clone https://github.com/Empire-Business/security-auditor \
  ~/.codex/skills/security-auditor
```

A skill aparece automaticamente na lista de skills do Codex.

---

## Como atualizar

Para baixar a versão mais recente, basta dizer ao Claude:

```
"atualiza a skill de segurança"
```

ou variações: `"update security-auditor"`, `"tem update da skill?"`, `"instala a nova versão"`.

O Claude busca o diff (`git fetch` + `log`), aplica **por tag/commit verificado** e te mostra o que mudou — nunca `git pull main` cego.

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

## Cobertura — 38 categorias-base + módulos v1.9

### P0 — Crítico (corrija hoje)
| # | Categoria |
|---|-----------|
| 1 | Segredos & Variáveis de Ambiente |
| 1b | service_role — remover e migrar para Access Tokens temporários |
| 1c | Enumeração de usuários via mensagens de erro *(v1.6)* |
| 1d | API keys e segredos de terceiros hardcoded no frontend *(novo v1.8)* |
| 2 | Git & .gitignore (segredos commitados) |
| 3 | Rotas privadas & autenticação |
| 3b | getSession() vs getUser() + CVE-2025-29927 |
| 3c | **Server Actions / Route Handlers como endpoints públicos** *(novo v1.7)* |
| 3d | **Brute force protection + CAPTCHA/Attack Protection** *(novo v1.8)* |
| 4 | Supabase RLS — tabelas sem proteção |
| 5 | Supabase Policies permissivas (USING true, IDOR) |
| 6 | Dependências com CVE crítico (tabela expandida v1.7) |
| 6b | **Assinatura de webhook** (Stripe/Svix/GitHub) — antes da idempotência *(novo v1.9)* |
| 6c | **IA/LLM — prompt injection, tool-calling abuse, RAG cross-tenant, token-DoS** *(novo v1.9)* |
| 6d | **Edge Functions (Deno) — verify_jwt, --no-check, import map, supply chain** *(novo v1.9)* |

### P1 — Alto (corrija esta semana)
| # | Categoria |
|---|-----------|
| 5b | RLS performance — (SELECT auth.uid()), índices e TO authenticated |
| 7 | Supabase Storage Buckets |
| 8 | Functions SECURITY DEFINER |
| 9 | Views que bypassam RLS |
| 10 | SSRF via pg_net |
| 11 | JWT — validação e ataques avançados |
| 11b | **JWT algorithm lock — ES256/JWKS vs HS256** *(novo v1.7)* |
| 12 | MFA — bypass + RESTRICTIVE policy pattern |
| 13 | Gerenciamento de sessão & logout |
| 13b | **Session fixation — rotação de session ID** *(novo v1.7)* |
| 14 | IDs sequenciais & IDOR |
| 15 | Sanitização de retornos de API (over-fetching) |
| 16 | Criptografia de dados sensíveis |
| 17 | CORS & Security Headers |
| 17b | **Cross-Origin Isolation — COEP, COOP, CORP** *(novo v1.7)* |
| 18 | Rate limiting & proteção anti-brute-force + honeypots |
| 18b | Input size limits — prevenção de DoS *(v1.6)* |
| 18c | Testes automatizados de segurança (TDD) *(v1.6)* |
| 19 | SQL Injection, XSS & Prototype Pollution |
| 19b | **ReDoS — regex com quantificadores aninhados** *(novo v1.7)* |
| 20 | Supabase Realtime & subscriptions |
| 20b | Lógica sensível exposta no frontend |
| 20c | .or() PostgREST injection |
| 20d | Realtime canais privados + RLS |
| 20e | **Zod .strict() para mass assignment + noUncheckedIndexedAccess** *(novo v1.7)* |
| 20f | **Data Access Layer + server-only + React Taint APIs** *(novo v1.7)* |
| 20g | **CSRF em Route Handlers** *(novo v1.7)* |
| 20h | **Open Redirect — validar redirectTo e next params** *(novo v1.7)* |
| 20i | **Password hashing seguro — bcrypt/Argon2id** *(novo v1.8)* |
| 20j | **Error handling seguro — fail-safe, não expor stack traces** *(novo v1.8)* |

### P2 — Médio (próximo sprint)
| # | Categoria |
|---|-----------|
| 21 | Upload de arquivos — MIME, magic bytes, IP trackers |
| 22 | CSP & Subresource Integrity |
| 22b | **Supply chain security — lockfile, npm ci, integridade** *(novo v1.8)* |
| 23 | console.log em produção & source maps |
| 24 | Supabase Vault & rotação de chaves |
| 25 | **Lógica de negócio & race conditions** (cenários reais) |
| 26 | **LGPD/GDPR — direitos do titular, consentimento, retenção, DPO, DPIA** *(ampliado v1.8)* |
| 27 | Logging, monitoramento & alertas |
| 27b | TypeScript types do Supabase |
| 27c | Schema exposure — schema private |
| 27d | **PII detection & data classification** *(novo v1.8)* |
| 27e | **Backup, disaster recovery & RTO/RPO** *(novo v1.8)* |

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
    ├── infrastructure.md       # OWASP Top 10, CSP, Dashboard hardening
    ├── v19-modules.md          # Módulos v1.9: IA/LLM, Edge/Deno, ORM, OAuth, lógica de borda, CI/CD
    └── hall-of-fame.md         # Red-team da própria skill: pódio e crédito dos agentes
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

### v1.7 — 2026-03-28
- Comando de auto-update SEGURO: `"atualiza a skill"` → `git fetch` + diff + pin por tag/commit verificado (nunca `git pull main` cego) + changelog
- 9 novas tasks P0/P1: Server Actions como endpoints públicos, JWT algorithm lock, session fixation, Cross-Origin Isolation, ReDoS, Zod `.strict()`, DAL + server-only + Taint APIs, CSRF Route Handlers, Open Redirect
- Tabela de CVEs expandida: CVE-2024-34351, CVE-2024-46982, CVE-2024-56332, GHSA-3529, jsonwebtoken < 9.0.0
- MFA RESTRICTIVE policy pattern + RLS `TO authenticated` audit

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

---

## Licença

MIT License — [ver LICENSE](./LICENSE).

> **Aviso importante:** esta skill realiza análises de segurança via IA. O autor não garante
> que todas as vulnerabilidades serão detectadas e não se responsabiliza por falhas de segurança,
> vazamentos de dados ou incidentes em apps auditados com ela. Auditorias geradas por IA não
> substituem revisão por profissional de segurança qualificado. Leia o [LICENSE](./LICENSE) completo.
