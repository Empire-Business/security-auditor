# Módulos v1.9 — cobertura ampliada (IA/LLM, Edge/Deno, ORM, OAuth, lógica de borda, CI/CD)

Complemento do `audit-details.md`. Cada módulo indica: **Procure**, **Risco**, **Correção**. Nasceu do red-team da própria skill (ver `hall-of-fame.md`).

## Índice
- [P0 — IA/LLM](#llm) · [Edge Functions/Deno](#edge) · [Assinatura de webhook](#webhook) · [SSRF server-side](#ssrf)
- [P1 — ORM/conexão direta](#orm) · [OAuth/OIDC](#oauth) · [Refresh token & sessões](#refresh) · [Cache/ISR autenticado](#cache) · [Mass-assignment (camada de privilégio)](#mass) · [Multi-tenant](#tenant) · [Unicode/homógrafos](#unicode) · [Dinheiro/precisão](#money) · [Races fora do financeiro](#races) · [Idempotência em toda mutação](#idem) · [Upload avançado](#upload) · [JWT edge cases](#jwt) · [Enumeração além do login](#enum) · [Batching p/ bypass de rate-limit](#batch) · [Image Optimizer](#image) · [Vercel preview/env](#vercel) · [CI/CD posture](#cicd) · [Monorepo env](#mono)
- [P2 — Residência de dados](#residency) · [Feature flags](#flags) · [i18n/locale](#i18n) · [A11y & privacidade](#a11y) · [E-mail descartável/plus](#disposable) · [Fan-out/amplificação](#fanout) · [HIBP & passkeys](#hibp)

---

## P0

### IA/LLM — prompt injection, tool-calling, RAG {#llm}
Apps vibe-coded quase sempre embutem IA (Vercel AI SDK `streamText`/`generateText`, `useChat`, tool/function calling, RAG com pgvector). A skill-base não olhava isso.

- **Procure**: `streamText|generateText|useChat|tool(|function calling|@ai-sdk|openai|pgvector|embedding`.
- **Risco**: prompt injection direto/indireto; vazamento de system prompt; tool `deleteUser`/`runSQL` chamável via prompt; RAG que cruza tenant (busca vetorial sem filtro `auth.uid()`); token-DoS (sem budget por usuário); PII/segredo enviado ao provider.
- **Correção**:
  - Tools com **allowlist + auth por tool** (a tool só roda se o usuário tem permissão real — checada no servidor, não no prompt).
  - RAG SEMPRE filtrado: `WHERE tenant_id = (SELECT auth.uid())` (ou filtro de RLS na tabela vetorial).
  - System prompt fora do alcance do usuário; nunca ecoe system prompt; trate conteúdo recuperado como **dado não confiável** (anti-injeção indireta).
  - **Budget/rate-limit de tokens por usuário**; cap de `maxTokens`; streaming com timeout.
  - Nunca enviar PII/segredos ao provider; redija antes.

### Edge Functions (Deno) {#edge}
- **Procure**: `supabase/functions/**/index.ts`, `deno.json`, `import_map`, `--no-check`, `verify_jwt`, imports `https://esm.sh/` e `npm:`.
- **Risco**: `verify_jwt = false` + `service_role` = endpoint público que bypassa RLS; `--no-check` mascara erros; imports `esm.sh`/`npm:` sem lockfile/SRI = supply chain; CORS fallback para `ALLOWED_ORIGINS[0]` vaza origem.
- **Correção**:
  - Proibir `verify_jwt = false` em funções que usam `service_role`; validar JWT (`getUser(token)`) no início.
  - Nunca deploy com `--no-check`; travar imports por `deno.lock`/`import_map` com versões pinadas.
  - Segredos via `supabase secrets` (não `.env` commitado); mover service_role para servidor.
  - CORS: se origin não casa, **rejeite** (não responda com outro origin).

### Assinatura de webhook {#webhook}
Ver `audit-details.md` → seção "Race conditions" (exemplo corrigido com `constructEvent`/`timingSafeEqual`/`svix`). **P0**: verificar assinatura ANTES da idempotência em todo webhook (Stripe, Svix, GitHub `X-Hub-Signature-256`, Supabase Database Webhooks). Idempotência atômica via `INSERT … ON CONFLICT` com `UNIQUE(event_id)` — nunca `select→insert` nem `new Set()` em serverless.

### SSRF server-side (além do pg_net) {#ssrf}
- **Procure**: `fetch(`/`axios(`/unfurl/preview/import com URL vinda do usuário em Route Handlers/Server Actions/Edge Functions; validador `z.string().url()` (não basta).
- **Risco**: `http://169.254.169.254/latest/meta-data/iam/...` (credenciais cloud), `localhost`/ranges privados, scan interno; redirect 302 → interno; DNS rebinding.
- **Correção**: allowlist de domínio (igualdade/`'.'+domain`); resolva DNS e **re-cheque o IP** recusando ranges privados/loopback/link-local (anti-rebinding); proíba redirects; bloqueie `169.254.169.254`, `127.0.0.0/8`, `10/8`, `172.16/12`, `192.168/16`, `fc00::/7`.

---

## P1

### ORM / conexão direta (Prisma/Drizzle/Kysely) {#orm}
- **Procure**: `prisma/schema.prisma`, `drizzle.config`, `kysely`, `$queryRaw`, `sql\`…\``, connection string com role `postgres`/`service_role`.
- **Risco**: RLS só protege `anon`/`authenticated` via PostgREST. Conexão direta com `postgres`/`service_role` **ignora RLS por completo**; `sql\`SELECT … WHERE id=${input}\`` vira SQLi + dump total.
- **Correção**: role dedicada com RLS + privilégios mínimos (nunca `postgres`/`service_role`); sempre parametrizado (`$queryRaw` com placeholders, Drizzle `sql` com bindings); auditar migrations que desligam RLS.

### OAuth/OIDC {#oauth}
- **Procure**: `signInWithOAuth`, `redirectTo`, `linkIdentity`, troca de `code`; ausência de PKCE/`state`/`nonce`.
- **Risco**: ATO por account pre-creation (provider sem verificação de e-mail + linking posterior); roubo de `code` sem PKCE; login CSRF sem `state`.
- **Correção**: PKCE obrigatório (clients públicos); validar `state` (CSRF) e `nonce` (OIDC); `redirect_uri` fixo no Dashboard; vinculação de identidade exigindo e-mail verificado.

### Refresh-token rotation, reuse-detection e sessões {#refresh}
- **Procure**: ausência de "minhas sessões", revoke, limite de sessões concorrentes, TTL/inatividade de refresh.
- **Risco**: refresh roubado reusável sem detecção; takeover persistente mesmo com MFA (MFA só no login).
- **Correção**: habilitar **Refresh Token Rotation + Reuse Detection** no Dashboard; endpoint "minhas sessões" com revoke; TTL curto; re-MFA em elevação de privilégio.

### Cache/ISR/SWR de dados autenticados {#cache}
- **Procure**: `unstable_cache`, `revalidate`, `export const dynamic`, `Cache-Control` em rotas que leem `cookies()`/`headers()`, CDN cacheando `Set-Cookie`.
- **Risco**: página/ISR do usuário A servida do cache para o B; `Set-Cookie` cacheado na CDN → sequestro de sessão / vazamento cross-user.
- **Correção**: proibir cache de rotas que usam `cookies()`/`headers()`; `Cache-Control: private, no-store` em dados autenticados; auditar cache key/tags e `generateStaticParams` com dados por usuário.

### Mass-assignment — camada de privilégio (além do Zod) {#mass}
`.strict()` protege só o endpoint que usa o schema. Defesa real é no banco.
- **Procure**: colunas `role|plan|is_admin|is_verified|price|stripe_*|owner_id|created_at` sem `REVOKE` de `authenticated`; `WITH CHECK` que não trava essas colunas no INSERT.
- **Correção**:
  ```sql
  REVOKE INSERT, UPDATE ON TABLE public.users FROM authenticated;
  GRANT UPDATE (display_name, avatar_url) ON TABLE public.users TO authenticated;
  -- ou WITH CHECK que rejeita colunas privilegiadas no INSERT:
  -- WITH CHECK (auth.uid() = user_id AND role IS NULL AND is_verified IS NULL)
  ```
  Teste: `PATCH /rest/v1/users {"role":"admin"}` deve falhar independente do Zod. `created_at`/`is_verified` via `DEFAULT`/trigger server-side.

### Multi-tenancy {#tenant}
- **Procure**: `tenant_id` lido de body/header/query (deve vir só do JWT); policy com `USING` mas **sem `WITH CHECK`** (permite mudar `tenant_id` no INSERT/UPDATE); ausência de teste cross-tenant A→B.
- **Correção**: `tenant_id` sempre do JWT (`app_metadata`); exigir `WITH CHECK` em toda policy de INSERT/UPDATE; teste pgTap/HTTP tenant A→B análogo ao de IDOR.

### Unicode / homógrafos / normalização {#unicode}
- **Procure**: `unique(username)`/`unique(email)` sem normalização; ausência de NFC/`lower()`/mapa de confusáveis.
- **Risco**: squatting (`joao` vs `joаo` cirílico), contas duplicadas (`café` vs `cafe\u0301`), bypass de bloqueio, farm de trial/voto.
- **Correção**: normalizar **NFC** + `lower()` + mapa de confusáveis antes de `unique`; tratar IDNA/punycode em domínios; teste que cria `alice` e rejeita `аlice`.

### Dinheiro / precisão {#money}
- **Procure**: `parseFloat`, `price * qty`/operações monetárias em `number` (IEEE-754) no servidor.
- **Risco**: `0.1+0.2`, cobrança a mais/menos, overflow via `9999999999999999`.
- **Correção**: armazenar em **centavos (`bigint`)** + `numeric` no banco; modo de arredondamento explícito; `amount` vem do DB, nunca do cliente.

### Race conditions fora do financeiro {#races}
- **Amplie a lista** de fluxos absurdos: oversell de estoque, double-vote/double-like (contador que dessincroniza), double-follow, reserva de assento/ingresso único, dois usuários reivindicando o mesmo `slug/username`.
- **Correção**: `UNIQUE` + transação; `SELECT … FOR UPDATE SKIP LOCKED` para filas; ordenação determinística de locks (anti-deadlock); `SERIALIZABLE` para invariantes multi-linha; `pg_advisory_lock` quando preciso.

### Idempotência em toda mutação {#idem}
- **Regra**: toda Server Action/Route Handler de mutação (criar post, seguir, votar, resgatar, convidar, transferir) tem **idempotency key** ou `UNIQUE` — não só pagamento.
- **Procure**: `export async function POST` sem `idempotency`/constraint.

### Upload avançado {#upload}
Magic bytes (8 bytes) não bastam.
- **Procure**: aceite de SVG/polyglot, PDF com `/JavaScript`, EXIF, extração de zip, limite só de bytes **comprimidos**.
- **Risco**: XSS via SVG/polyglot; vazamento de GPS (EXIF); zip-slip na extração; **decompression/dimension bomb** (1KB gzip→1GB; PNG 1×1 que decodifica enorme).
- **Correção**: re-renderizar/sanitizar (não confiar em magic bytes); servir tipos ativos com `Content-Disposition: attachment` + CSP sandbox; strip de EXIF; bloquear `..` em extração; limite de tamanho **decodificado** (pixels/dimensões), não só de upload.

### JWT — edge cases {#jwt}
- **Procure**: validação só de `alg`/assinatura; ausência de `exp`/`nbf`/`jti`; `kid` livre; refresh sem rotação.
- **Risco**: replay de link de convite/reset; `kid` injection (path traversal/SQLi no header); sessões quase eternas.
- **Correção**: validar `exp`/`nbf`/`jti` (anti-replay); allowlist de `kid`/JWKS; TTL curto de access token; refresh rotation + reuse-detection.

### Enumeração além do login {#enum}
- **Procure**: endpoint de "verificar disponibilidade de username/e-mail", convite/compartilhamento, busca-por-e-mail que revelam existência por **status/tamanho/tempo**.
- **Correção**: resposta uniforme (mesma mensagem/status/tempo) em availability-check, convite e busca; aplicar DUMMY_HASH/const-time além do login.

### Batching/arrays para bypass de rate-limit {#batch}
- **Procure**: `.insert([...])`, `ids:[]`, `.rpc` em massa, `Prefer: count`, endpoint GraphQL — "10 req/min" com 10k ops dentro de 1 req.
- **Correção**: limitar **tamanho de arrays/body** por endpoint e contar **operações** (não só requests) no rate limit.

### Next.js Image Optimizer {#image}
- **Procure**: `images.remotePatterns`/`domains` ausentes ou permissivos; `/_next/image?url=`.
- **Risco**: SSRF via otimizador; DoS por amplificação.
- **Correção**: restringir `remotePatterns` ao próprio Storage/CDN; limitar tamanhos e `minimumCacheTTL`.

### Vercel — preview, env por ambiente, proteção {#vercel}
- **Procure**: previews públicos apontando para Supabase de produção; `service_role` em env de Preview; `VERCEL_AUTOMATION_BYPASS_SECRET` vazado; ausência de Deployment Protection.
- **Correção**: escopo de env (Production vs Preview); **nunca** `service_role` em Preview; ativar Deployment Protection; rotacionar bypass secret; `X-Robots-Tag: noindex` fora de prod; tratar preview como superfície pública.

### CI/CD posture {#cicd}
Ver `infrastructure.md` → "GitHub Actions" (hardening v1.9). Checklist: `permissions: contents: read`; banir `pull_request_target` com secrets; OIDC para deploy; pin por SHA; branch/environment protection; revisar artefatos entre jobs.

### Monorepo / compartilhamento de .env {#mono}
- **Procure**: `turbo.json` `globalEnv`/`env`, `nx.json`, `dotenv -e ../../.env`, `.env` na raiz herdado por `apps/*`/`packages/*`.
- **Risco**: `service_role` na raiz entra no bundle de um pacote client por herança.
- **Correção**: escopo de `.env` por pacote; estender grep de segredos a `packages/**`, `apps/**`; auditar `globalEnv`.

---

## P2

### Residência de dados / transferência internacional {#residency}
- **Procure**: região do projeto Supabase; PITR/logs/read replicas cross-border; Vercel Functions/Edge globais; OpenAI/Sentry (EUA) sem base legal.
- **Correção**: escolher região compatível com LGPD; mapear cada processador estrangeiro com base do art. 33; cuidado: "cópia em região secundária" pode violar residência.

### Feature flags / remote config {#flags}
- **Procure**: SDKs client (LaunchDarkly/GrowthBook/PostHog) expondo flags de autorização; `if (flags.isPro)` só no client; targeting por `user.email`.
- **Correção**: proibir flags de autorização no client; avaliar gates no servidor; nunca enviar PII como targeting key.

### i18n / locale {#i18n}
- **Procure**: matcher do middleware que não cobre `/en/dashboard`; `Accept-Language`/`?locale=` manipulando preço/lógica; mensagens de erro diferentes por idioma.
- **Correção**: incluir locales no matcher; validar `locale` contra allowlist; mensagens de erro idênticas em todos os idiomas.

### Acessibilidade & privacidade {#a11y}
- **Procure**: `aria-label`/`title`/live regions com PII; máscara visual (`••••`) com valor real no DOM/`aria-label`.
- **Correção**: máscara visual == máscara no DOM; não anunciar dados sensíveis via `aria-live`.

### E-mail descartável / plus-addressing {#disposable}
- **Procure**: unicidade de e-mail sem canonicalização.
- **Correção**: canonicalizar (remover `+alias`, dots em Gmail, `lower()`) + lista de domínios descartáveis antes de `unique`/signup (frena farm de trial/voto/indicação-a-si-mesmo).

### Fan-out / amplificação {#fanout}
- **Procure**: 1 ação que dispara N efeitos (notificar todos os seguidores, e-mail por membro, webhook em cascata).
- **Correção**: cap de destinatários, debounce, cota por usuário; auditar triggers que enviam e-mail/notificação em loop.

### HIBP & passkeys {#hibp}
- **Correção**: habilitar **Leaked Password Protection (HaveIBeenPwned)** + força mínima no Dashboard Auth; adotar **WebAuthn/passkeys** (resistente a phishing) e binding de sessão a dispositivo.
