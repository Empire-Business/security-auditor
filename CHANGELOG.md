# Changelog — security-auditor

Histórico de versões e melhorias da skill. Ao fazer qualquer atualização futura, registre aqui a versão, data e o que foi adicionado/modificado.

---

## Não lançado (edição local, ainda sem tag/versão)

### Modo Pentest — squad de agentes adversariais competitivos (oferecido, opt-in)

Ajuste pedido pelo usuário: ao rodar a verificação de segurança, a skill deve oferecer um pentest multi-agente onde cada agente é "recompensado" por falhas reais encontradas, com framing rigoroso e faminto por achar problemas.

### Adicionado
- **Nova seção "Oferta de Modo Pentest"** (antes do Passo 0): sempre que um trigger de auditoria dispara, a skill oferece (nunca ativa sozinha) rodar um squad de 3-5 agentes adversariais em paralelo, cada um com uma lente diferente (autorização/IDOR, injeção, lógica de negócio/race conditions, segredos, supply-chain).
- **Sistema de pontuação com salvaguarda anti-reward-hacking**: pontos só são atribuídos após verificação independente do achado (mesmo padrão de re-teste + re-query já usado na skill); achado não verificado marca "reportado, não confirmado" e vale zero pontos — evita que o incentivo de "recompensa" leve agentes a inventar vulnerabilidades falsas para pontuar. Pontuação por severidade (P0 > P1 > P2), duplicata entre agentes conta uma vez.
- **Relatório do Modo Pentest**: placar por agente/lente, achados confirmados vs. não confirmados, e o valor incremental (achados que o squad pegou e a auditoria sistemática sozinha não pegaria). Achados confirmados entram na mesma pipeline de correção e gate `verdict.json` já existentes — sem regras de gate diferentes.
- **Passo 4.5 (Red Team single-agent)** agora referencia o Modo Pentest como a versão ampliada do mesmo adversarial testing.
- **Trigger phrases** no frontmatter ganham "pentest", "modo pentest", "esquadrão de agentes de segurança".

### Nota
Esta entrada ainda não foi commitada nem tagueada no repositório `Empire-Business/security-auditor` — é uma edição local. Propagação para outras máquinas/projetos depende do fluxo de update verificado (tag/SHA pinado) já existente na skill.

---

## v1.10 — 2026-07-10

### Contrato de integração + update verificado de verdade (red-team da integração)

Esta versão nasce do segundo red-team, agora sobre a **costura** com a `omnx-code`: o endurecimento v1.9 estava declarado, mas não era imposto nem verificável. Pódio e crédito em `references/hall-of-fame.md` (Rodada 2).

### Adicionado
- **`security-report/verdict.json` (contrato de gate, machine-readable)**: ao final de toda auditoria, a skill agora grava um JSON com schema fixo (`contract_version`, `p0_open`, `p1_open`, `not_verified_open`, `manual_open`, `fix_applied`, `gate`). Regra fail-closed: `gate = PASS` só se `p0_open == 0` E `p1_open == 0` E `not_verified_open == 0` E `manual_open == 0`. É o artefato que a `omnx-code` lê para bloquear deploy.
- **Frontmatter estruturado**: `version: "1.10"` e `contract_version: 1` (leitura por máquina, não mais por grep em CHANGELOG).
- **Allowlist de referência imutável** no fluxo de update (`PINNED_TAG=`/`PINNED_SHA=`), para quando houver release assinado.

### Modificado
- **Corpo alinhado ao contrato report-only**: títulos de task renomeados de "Auditar e corrigir" para "Auditar e propor" (54 ocorrências); `README.md` agora descreve o ciclo AUDITAR → PROPOR → (CORRIGIR só com confirmação) → VERIFICAR e menciona o `verdict.json`.
- **Update verificado de verdade**: `git verify-tag <TAG> && git checkout <TAG>` (verificar ANTES de trocar o código); removido o `|| echo` que mascarava falha; `git fetch --tags` padronizado; em conflito, para e pede ao usuário (sem `git pull --ff-only` automático). Sem tag assinada, o fluxo PARE e pede um SHA explícito — nunca deriva "a mais recente", nunca fica em `main`.
- **Dono do verbo "atualizar"** declarado: este fluxo atualiza só a `security-auditor`; "atualizar tudo" é da `omnx-code`.
- **Release carimbado (`v1.10.0`)**: tag anotada publicada; fluxo de update agora usa `PINNED_TAG=v1.10.0` + `PINNED_SHA=41fd0d6...`, validando a tag pelo SHA imutavel (nunca 'tag mais alta', nunca `main`); `git verify-tag` e usado se um dia houver GPG.

### Segurança
- Fecha o teatro de "auto-update assinado": antes, `git checkout <ref> && git verify-tag … || echo` aplicava o código antes de verificar (e, sem tags assinadas, caía sempre no aviso). Agora verifica antes e aborta sem referência imutável.

---

## v1.9 — 2026-07-10

### Endurecimento completo (red-team da própria skill)

Esta versão nasce de um exercício de **red-team contra a própria skill** (6 agentes atacantes). O foco foi: parar de ensinar conselho errado, trocar "verificação por grep" por verificação real, fechar o supply-chain da própria skill e ampliar o escopo para as superfícies de 2025. Crédito e pódio em `references/hall-of-fame.md`.

### Corrigido — conselho errado/perigoso (P0/P1)
- **RPC "seguro" virava roubo de saldo**: `process_purchase`/`deduct_balance_atomic` reescritos com `SECURITY DEFINER`, `p_buyer_id = auth.uid()`, `CHECK (amount > 0)` e `REVOKE EXECUTE FROM anon, authenticated` (valor negativo não vira mais auto-crédito).
- **Webhook sem assinatura**: verificação (`constructEvent`/`timingSafeEqual`/`svix`) agora é etapa P0 **anterior** à idempotência; exemplo corrigido.
- **`getSession()` nos próprios exemplos**: substituído por `getUser()` + `@supabase/ssr` em `audit-details.md` (page.tsx, MFA). `auth-helpers-nextjs` marcado como deprecado.
- **AAL de MFA** derivado de `factors.length` (errado) → `supabase.auth.mfa.getAuthenticatorAssuranceLevel()`.
- **CSRF** `origin.includes(host)` (bypass por substring) → `new URL(origin).host === host`.
- **Hook RBAC** sem `SECURITY DEFINER` (virava "todo mundo member") → corrigido; claim gravada em `app_metadata.user_role` e leitura TS alinhada.
- **CSP teatro**: removido `'unsafe-inline'` de `script-src`/`style-src` (nonce + `'strict-dynamic'`), `img-src` com allowlist, `object-src 'none'`; **removido** o header deprecado `X-XSS-Protection`.
- **Rate-limit/honeypot** com `x-forwarded-for` spoofável → IP confiável (`request.ip`/cadeia) + chave composta; honeypot não auto-bane por header.
- **Teste de IDOR** esperava `403` (RLS devolve `200`/vazio) → asserção no corpo (`data.length === 0` / não contém `victimId`).
- **LGPD**: prazo de notificação à ANPD corrigido de "72h" para **3 dias úteis** (Res. CD/ANPD 15/2024).
- **Tabela de CVEs** revisada: CVE-2025-66478 (faixas por linha menor 15.0.5/15.1.9/15.2.6/15.3.6/15.4.8/15.5.7/16.0.7), CVE-2025-55182 (pacote correto `react-server-dom-*`), CVE-2024-56332 reclassificado como DoS/DoW. ⚠️ CVEs mudam — re-verificar em fonte primária antes de auditar.
- Diversos: Argon2 com parâmetros OWASP, `pgp_sym_encrypt` (tipo `bytea` + chave via Vault + índice HMAC), `ON CONFLICT` com pré-requisito `UNIQUE`, Realtime em API v2 (`channel().on('postgres_changes')`), `SET search_path = ''` padronizado, grep de `select('*')` corrigido.

### Adicionado — verificação real (Eixo 2)
- **VERIFICAR** deixa de ser "busca rápida": exige **re-teste da vulnerabilidade** (prova de exploração negativa) e **re-query no banco** (`pg_tables.rowsecurity`, `pg_policies`) antes de marcar a task como concluída.
- **Scanners integrados ao fluxo** (não mais "complementares"): Semgrep/CodeQL (taint), Gitleaks (segredos), Trivy/`npm audit` (SCA), OWASP ZAP (DAST contra o deploy).
- **Fase 2 renomeada** para "Integridade de build" (não prova segurança); roda por **opt-out** quando houve edição; usa `--ignore-scripts` e ambiente sem segredos; corrigido `tsc --isolatedModules <arquivo>` (flag errada).

### Adicionado — threat model e escopo honesto (Eixo 3)
- **Passo 0 — Threat model (STRIDE)** antes do checklist fixo; repondera e reordena as tasks por app.
- **Escopo e limites** declarados no frontmatter e no topo do relatório (não cobre IA internals, mobile, ORM fora do supabase-js, CI/CD posture, PCI/HIPAA/SOC2).
- **Pontuação objetiva** ancorada em ASVS/CVSS/EPSS com rubrica e pesos (substitui o "X.X/10" subjetivo); declara % de cobertura ASVS.
- **Baseline/regressão**: lê o `audit-*.md` anterior e computa diff (novos/corrigidos/regredidos).
- Estados novos no relatório: **"FP confirmado"** e **"Não verificado"** (além de ✅/❌/⚠️/➖).

### Adicionado — novos módulos de cobertura (Eixo 4) em `references/v19-modules.md`
- **IA/LLM (P0)**: prompt injection, tool-calling abuse, RAG cross-tenant, token-DoS.
- **Edge Functions/Deno (P0)**: `verify_jwt=false`, `--no-check`, import map, supply chain `esm.sh`/`npm:`.
- **ORM/conexão direta (P1)**: Prisma/Drizzle/Kysely que bypassam RLS; role dedicada.
- **Auth moderna (P1)**: OAuth/OIDC (PKCE/state/nonce/linking), refresh-token rotation + reuse-detection, HIBP, passkeys/WebAuthn, gestão de sessões.
- **Lógica & borda (P1)**: mass-assignment na camada de privilégio, multi-tenant (teste A→B, `WITH CHECK`), Unicode/homógrafos, dinheiro em centavos, races de estoque/voto/like, idempotência em toda mutação, upload avançado (polyglot/SVG/EXIF/zip-slip/limite decodificado).
- **CI/CD & Vercel (P1)**: `GITHUB_TOKEN` mínimo, banir `pull_request_target` com secrets, OIDC, pin por SHA; Deployment Protection, env por ambiente, sem `service_role` em Preview.

### Adicionado — Guardrails v2 + supply-chain da própria skill (Eixo 5)
- **Auto-update seguro**: pin por tag/commit, `git verify-tag`/Sigstore antes de aplicar; **removido** o fallback `rm -rf … && git clone`; nunca `git pull main` cego.
- **Anti-prompt-injection**: bloco no topo — conteúdo de arquivos é **dado não confiável**, nunca instrução; Passo 4.5 (Red Team) **só reporta** (sem auto-fix).
- **Lista de operações destrutivas** (`REVOKE/ALTER/DROP/DELETE/SET SCHEMA/ENABLE RLS sem policy/filter-repo/BFG/rm -rf`) exigindo diff + confirmação + branch/stash obrigatório.
- **Redação por padrão**: não ler `.env` real para o contexto; `security-report/` com `chmod 600`, nome não-previsível, segredos/PoC mascarados.
- **Modo report-only como padrão** (auto-fix opt-in); `allow_implicit_invocation` revisto.

### Modificado
- Frontmatter `description`: escopo honesto, versão v1.9, modo AUDITAR→PROPOR (auto-fix opt-in).
- Missão (linha de abertura): "encontrar vulnerabilidades reais e propor/aplicar correções com verificação real".

> Crédito: AGENTE 2 (Auditor de Correção) 🥇, AGENTE 6 (Lógica & Borda) 🥈, AGENTE 5 (Atacante da Própria Skill) 🥉 — ver `references/hall-of-fame.md`.

---

## v1.8 — 2026-06-17

### Adicionado — LGPD, guardrails e segurança ampliada

- **Nova task `1d` [P0]**: API keys e segredos de terceiros hardcoded no frontend (OpenAI, Stripe, Google Maps, SendGrid)
- **Nova task `3d` [P0]**: Brute force protection — account lockout + CAPTCHA/Attack Protection no Supabase Auth
- **Nova task `20i` [P1]**: Password hashing seguro — Argon2id/bcrypt/PBKDF2 em auth customizada; alerta para MD5/SHA-1/SHA-256
- **Nova task `20j` [P1]**: Error handling seguro — fail-safe defaults, não exposição de stack traces, OWASP A10:2025
- **Nova task `22b` [P2]**: Supply chain security — lockfile, `npm ci`, verificação de integridade, OWASP A03:2025
- **Task `26` [P2] totalmente reescrita**: LGPD/GDPR completo — direitos do titular (art. 18), consentimento, finalidade, minimização, retenção, DPO, DPIA, notificação de incidentes, hard delete vs soft delete
- **Nova task `27d` [P2]**: PII detection & data classification — mapeamento de dados pessoais no banco
- **Nova task `27e` [P2]**: Backup, disaster recovery & RTO/RPO
- **Tabela de CVEs expandida**: adicionados CVE-2025-66478, CVE-2025-55183, CVE-2025-55184, CVE-2025-67779 e CVE-2025-48757
- **Modo Preventivo ampliado**: novo template de LGPD/privacidade por design
- **Guardrails da própria skill**: seção obrigatória de comportamento seguro do auditor — não executar comandos destrutivos sem confirmação, não modificar segredos reais, proteger PII durante auditoria, fail-safe, transparência
- **Arquivos de referência atualizados**:
  - `references/audit-details.md`: novas seções de Password hashing, Error handling, Supply chain, Brute force, LGPD completo, PII detection, Backup e DR
  - `references/infrastructure.md`: OWASP Top 10 atualizado para 2025, seções de LGPD/GDPR e Supply chain
- **Triggers ampliados**: adicionados "audita LGPD", "verifica privacidade", "checkup de segurança"

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
