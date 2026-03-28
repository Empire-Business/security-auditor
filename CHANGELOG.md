# Changelog — security-auditor

Histórico de versões e melhorias da skill. Ao fazer qualquer atualização futura, registre aqui a versão, data e o que foi adicionado/modificado.

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
