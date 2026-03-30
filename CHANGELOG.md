# Changelog — security-auditor

Histórico de versões e melhorias da skill. Ao fazer qualquer atualização futura, registre aqui a versão, data e o que foi adicionado/modificado.

---

## v1.7 — 2026-03-28

### Adicionado — pesquisa web completa sobre segurança Supabase + TypeScript 2024/2025

- **Comando de auto-update do GitHub**: nova seção no final do SKILL.md — usuário pode dizer "atualiza a skill" e o Claude executa `git pull origin main` + mostra changelog
- **Nova task `3c` [P0]**: Server Actions e Route Handlers como endpoints públicos — verificar que cada um re-autentica independente do middleware; grep por `'use server'` sem `auth.getUser()`
- **Nova task `11b` [P1]**: JWT algorithm lock — auditar ES256/JWKS vs HS256; verificar `jsonwebtoken < 9.0.0`; tabela de CVEs relacionados
- **Nova task `13b` [P1]**: Session fixation — rotação de session ID após login e elevação de privilégio com `auth.refreshSession()`
- **Nova task `17b` [P1]**: Cross-Origin Isolation headers (COEP + COOP + CORP) — proteção contra Spectre, XS-Leaks e timing attacks
- **Nova task `19b` [P1]**: ReDoS prevention — grep por regex com quantificadores aninhados (`(a+)+`, `([a-z]+)*`); correção via Zod + limites explícitos
- **Nova task `20e` [P1]**: Zod `.strict()` para mass assignment prevention + `noUncheckedIndexedAccess` no `tsconfig.json`
- **Nova task `20f` [P1]**: Data Access Layer (DAL) + `server-only` package + React Taint APIs (`experimental_taintObjectReference`)
- **Nova task `20g` [P1]**: CSRF em Route Handlers — verificar `origin` header em POST/PUT/DELETE
- **Nova task `20h` [P1]**: Open Redirect — validar `redirectTo`, `next`, `returnTo` params contra allowlist de paths relativos
- **Enriquecida task `#6` CVE**: tabela expandida com CVE-2024-34351 (SSRF), CVE-2024-46982 (cache poisoning), CVE-2024-56332 (RCE via RSC), GHSA-3529 (GoTrue email link poisoning self-hosted), jsonwebtoken < 9.0.0
- **Enriquecida task `#12` MFA**: adicionado padrão `AS RESTRICTIVE` explícito para policies de MFA — garante que nenhuma outra policy PERMISSIVE pode bypassar o requisito de MFA
- **Enriquecida task `#5b` RLS performance**: adicionada verificação da cláusula `TO authenticated` explícita em todas as policies
- **Triggers de auto-update** adicionados ao frontmatter `description` do SKILL.md

---

## v1.6 — 2026-03-28

### Adicionado — insights de pentest real em 4 sistemas vibe-coded

- **Modo Preventivo**: nova seção antes do Passo 1 com prompt template para usar a IA com segurança desde o início ("Este sistema será submetido a pentest...")
- **Nova task `1c` [P0]**: Enumeração de usuários via mensagens de erro de autenticação
  - Grep patterns para detectar mensagens específicas ("email não encontrado", "senha incorreta")
  - Correção com mensagem genérica + proteção contra timing attack em auth customizada
  - Padrão seguro para endpoint de recuperação de senha
- **Nova task `18b` [P1]**: Limite máximo de tamanho para todos os inputs (DoS prevenção)
  - Auditoria via Grep em schemas Zod sem `.max()`
  - SQL para detectar colunas TEXT sem constraint de tamanho
  - Templates Zod com limites por tipo de campo
  - CHECK constraints no banco como segunda linha de defesa
- **Nova task `18c` [P1]**: Testes automatizados de segurança (TDD approach)
  - Template de testes de IDOR (usuário A não acessa recursos do B)
  - Testes de autenticação (401 sem token, 401 com token inválido)
  - Testes de validação de input (oversized, XSS)
- **Enriquecida task 18** (Rate limiting): diferenciação de limites por endpoint + honeypots como defesa ativa
- **Enriquecida task 21** (Upload): URLs externas como IP trackers — validação de domínio permitido
- **Enriquecida task 25** (Lógica de negócio): cenários concretos de exploração (compra+reembolso+comissão, race condition de estado, recurso infinito combinando ações legítimas)
- **Passo 4.5 na Fase 2**: Red Team — prompt template para usar Claude como atacante contra o próprio sistema após auditoria
- **`references/audit-details.md`**: adicionadas seções completas de Enumeração de usuários, Input size limits, Rate limiting honeypots, Testes de segurança (templates), Race conditions (cenários e função atômica com idempotency)

---

## v1.5 — 2026-03-28

### Adicionado
- **Fase 2 — Verificação de integridade do app**: após concluir todos os reparos, a skill agora para e pede autorização ao usuário para executar uma bateria de testes de integridade
- A Fase 2 detecta scripts disponíveis (`tsc`, `build`, `lint`, `test`, `test:e2e`) via `package.json`
- Execução paralela das verificações usando TaskCreate por script
- Verificação focada nos arquivos modificados durante a auditoria
- Relatório final da Fase 2 com tabela de status por verificação
- Se alguma verificação falhar por causa de uma correção de segurança, a skill corrige e re-verifica antes de encerrar

---

## v1.4 — 2026-03-28

### Adicionado
- **Nova task `1b` [P0]**: "service_role — remover do projeto e migrar para Access Tokens temporários (7 dias)"
- **Nova categoria `1b`** no guia de auditoria com:
  - Explicação do risco permanente da `service_role` key
  - Instrução para criar **Supabase Access Tokens** com expiração de 7 dias (Dashboard → Account → Access Tokens)
  - **Ritual semanal de renovação**: lembrete toda segunda-feira com 3 passos (gerar, atualizar CI/CD, revogar anterior)
  - Grep pronto para detectar `service_role` fora das pastas permitidas
  - Plano de ação emergencial se encontrar a chave exposta
- Atualizada a **Filosofia** no topo: SERVICE_ROLE_KEY agora descrita como chave a evitar ao máximo, com referência direta aos Access Tokens temporários

---

## v1.3 — 2026-03-28

### Adicionado
- **5 novas tasks** no checklist: `3b`, `5b`, `20c`, `20d`, `27c`
- **Novo arquivo** `references/advanced-rls.md`:
  - Padrões multi-tenant (user_id, tenant_id via JWT, equipes/orgs com `has_role_on_account()`)
  - Performance: `(SELECT auth.uid())` vs `auth.uid()` (até 1000x mais rápido)
  - Índices obrigatórios em colunas de políticas RLS
  - Event trigger `rls_auto_enable()` para auto-habilitar RLS em novas tabelas
  - Tabela de comportamentos silenciosos do RLS (SELECT/UPDATE/DELETE sem erro)
  - RBAC via Custom Access Token Hook (SQL completo)
  - `app_metadata` vs `user_metadata` — distinção crítica para autorização
  - pgTap testing com `basejump-supabase_test_helpers`
- **Novo arquivo** `references/infrastructure.md`:
  - OWASP Top 10 mapeado ao Supabase/Next.js
  - CSP header completo para `next.config.ts` e `vercel.json`
  - Dashboard hardening checklist (conta, banco, Auth, Realtime, API)
  - Rate limits padrão do Supabase Auth (6 endpoints)
  - GitHub Actions security scan (`.github/workflows/security.yml`)
  - Schema exposure: schema `private`, revogação de permissões de `anon`/`authenticated`
- **Atualizações em** `references/audit-details.md`:
  - `getSession()` vs `getUser()` — anti-padrão crítico com exemplos de código
  - CVE-2025-29927 — middleware Next.js não é fronteira de segurança
  - `.or()` PostgREST injection — exemplo perigoso vs seguro
  - Realtime `private: true` + políticas para `realtime.messages`
  - Storage signed URLs + path traversal via policy
- **Categorias expandidas** em SKILL.md:
  - `3b` — getSession() vs getUser() + CVE-2025-29927
  - `5b` — RLS performance e índices obrigatórios
  - `20c` — `.or()` PostgREST injection
  - `20d` — Realtime canais privados + RLS em realtime.messages
  - `27c` — Schema exposure + permissões desnecessárias de anon
- **Tabela de arquivos de referência** adicionada ao final do SKILL.md

---

## v1.2 — 2026-03-28

### Adicionado
- **Filosofia de segurança** no topo do SKILL.md (zero-trust no cliente)
- **Categoria 1** expandida: verificação extra de `SERVICE_ROLE` em componentes React
- **Categoria 8** expandida: arquitetura `client.ts` / `server.ts` + fluxo seguro em Edge Functions
- **Nova categoria `20b`** — Arquitetura cliente-servidor: lógica sensível exposta no frontend (cálculos de preço, verificações de permissão, Server Actions)
- **Nova categoria `27b`** — TypeScript types do Supabase: geração de tipos com Supabase CLI, eliminação de `any` em código de banco de dados
- `security-report/` adicionado à verificação do `.gitignore` (categoria 2)

---

## v1.1 — 2026-03-28

### Adicionado
- **Passo 3 — Relatório final** completo: a skill agora gera automaticamente um relatório de auditoria em `security-report/audit-YYYY-MM-DD.md`
- Estrutura obrigatória do relatório com 6 seções: Estado do Sistema, Diagnóstico, Correções Aplicadas, Ações Manuais, Pontuação de Segurança, Próximos Passos
- Verificação obrigatória de `.gitignore` para garantir que `security-report/` não vai para o repositório
- Task `#28` adicionada ao checklist como tarefa final de relatório

---

## v1.0 — data original

### Inicial
- Auditoria de 27 categorias de segurança organizadas em P0/P1/P2
- Ciclo AUDITAR → CORRIGIR → VERIFICAR por categoria
- Cobertura: secrets, git, autenticação, RLS, policies, dependências, storage, edge functions, JWT, MFA, sessão, IDOR, CORS, rate limiting, XSS, SQL injection, Realtime, uploads, CSP, console.log, Vault, race conditions, LGPD, logging
- SQL pronto para executar no Supabase Dashboard para cada categoria aplicável
- Stack: React + TypeScript + Supabase + Vercel / Next.js

---

## Como registrar uma nova versão

Ao fazer qualquer atualização na skill, adicione uma entrada no topo deste arquivo seguindo o padrão:

```markdown
## vX.Y — YYYY-MM-DD

### Adicionado
- [o que foi adicionado]

### Modificado
- [o que foi alterado em algo existente]

### Removido
- [o que foi deletado]

### Corrigido
- [bugs ou comportamentos errados corrigidos]
```

Use **vX.Y** onde X é versão major (mudanças grandes de arquitetura) e Y é minor (novas features ou melhorias). Bump minor para adições; bump major para refatorações completas.
