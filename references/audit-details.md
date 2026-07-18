# Detalhes de Auditoria por Categoria

Referência completa com SQL queries, padrões de código e exemplos de correção para cada categoria do security-auditor.

## Índice
- [Seções P0 — Crítico](#p0)
- [Seções P1 — Alto](#p1)
- [Seções P2 — Médio](#p2)
- [Ferramentas complementares](#ferramentas)

> **v1.6:** Adicionadas seções — Enumeração de usuários, Input size limits, Rate limiting honeypots, Race conditions (cenários concretos), Upload (IP trackers), Testes de segurança TDD
> **v1.11:** Adicionadas seções — Criação de usuário com senha temporária, Recuperação de senha (token), Login via código OTP

---

## P0 — Crítico {#p0}

### Segredos & Variáveis de Ambiente

**Padrões a buscar no código (Grep):**
```
pattern: (SUPABASE_SERVICE_ROLE|SERVICE_KEY|JWT_SECRET|STRIPE_SECRET|sk_live|sk_test|eyJ[A-Za-z0-9_-]{20,})
files: **/*.ts, **/*.tsx, **/*.js, **/*.env*
```

**Variáveis seguras vs perigosas:**
- `NEXT_PUBLIC_SUPABASE_URL` — OK (URL pública do projeto)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` — OK (chave pública por design)
- `NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY` — CRÍTICO (nunca deve ser pública)
- `VITE_SUPABASE_SERVICE_KEY` — CRÍTICO
- `NEXT_PUBLIC_STRIPE_SECRET_KEY` — CRÍTICO

**Correção .env.example:**
```
# .env.example (sem valores reais)
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...
SUPABASE_SERVICE_ROLE_KEY=<service-role-key-nunca-exposta>
STRIPE_SECRET_KEY=<stripe-secret-nunca-exposta>
```

---

### Git — Segredos no histórico

**Verificar arquivos rastreados que deveriam estar ignorados:**
```bash
git ls-files | grep -E "\.env|\.key|\.pem|\.sqlite|\.db$"
```

**Verificar histórico de commits por arquivos .env:**
```bash
git log --all --full-history -- "*.env" "*.env.local" "*service_role*"
```

**Se encontrou secrets no histórico:**
1. Alerte o usuário — o histórico git é permanente mesmo após remoção
2. As chaves DEVEM ser revogadas e regeneradas no Supabase/Stripe Dashboard
3. Para limpar histórico (se necessário): `git filter-repo` ou `BFG Repo Cleaner`

**Entradas obrigatórias no .gitignore:**
```
.env
.env.local
.env.*.local
.env.production
.env.staging
node_modules/
.next/
dist/
build/
*.log
.DS_Store
coverage/
*.pem
*.key
*.p12
*.sqlite
*.db
security-report/
```

> `security-report/` é obrigatório: o relatório de auditoria pode conter detalhes de vulnerabilidades encontradas e nunca deve ser commitado.

---

### Enumeração de usuários

Formulários de autenticação que retornam mensagens diferentes para e-mail inexistente vs. senha errada permitem que atacantes enumerem usuários cadastrados automaticamente.

**Padrões a buscar:**
```bash
grep -rn "não encontrado\|not found\|email.*inexistente\|email.*not.*exist\
\|user.*not.*found\|invalid email\|wrong password\|senha incorreta\
\|incorrect password\|no account\|conta não existe" \
  src/ app/ pages/ --include="*.ts" --include="*.tsx" --include="*.js"
```

**Também verificar endpoint de recuperação de senha:**
```bash
grep -rn "reset.*password\|forgot.*password\|recuperar.*senha\|redefinir.*senha" \
  src/ app/ --include="*.ts" --include="*.tsx" -l
```
Inspecionar: o endpoint retorna "e-mail não encontrado" ou uma mensagem genérica?

**Correções por contexto:**

Login (Supabase Auth):
```typescript
// Supabase Auth já retorna erro genérico por padrão:
const { error } = await supabase.auth.signInWithPassword({ email, password })
// error.message = "Invalid login credentials" — ✅ genérico
// NÃO customizar essa mensagem para ser mais específica
if (error) return { error: "Credenciais inválidas. Verifique seu e-mail e senha." }
```

Auth customizada (se o projeto não usa Supabase Auth):
```typescript
// ❌ Vulnerável
const user = await db.users.findOne({ email })
if (!user) return { error: "E-mail não encontrado" }         // revela existência
if (!await bcrypt.compare(password, user.password_hash))
  return { error: "Senha incorreta" }                         // revela que e-mail existe

// ✅ Seguro — mesma mensagem, mesmo tempo de resposta
const user = await db.users.findOne({ email })
const passwordMatch = user
  ? await bcrypt.compare(password, user.password_hash)
  : await bcrypt.compare(password, DUMMY_HASH) // previne timing attack
if (!user || !passwordMatch)
  return { error: "Credenciais inválidas. Verifique seu e-mail e senha." }
```

Recuperação de senha:
```typescript
// ❌ Vulnerável
const user = await db.users.findOne({ email })
if (!user) return { error: "Nenhuma conta encontrada com esse e-mail" }

// ✅ Seguro — sempre a mesma resposta
return { message: "Se esse e-mail estiver cadastrado, você receberá um link em breve." }
// (enviar e-mail em background apenas se o usuário existir)
```

**Nota sobre Supabase Auth**: se usando `supabase.auth.resetPasswordForEmail()`, o Supabase já retorna resposta genérica por padrão. Não altere esse comportamento.

---

### Rotas privadas — Next.js App Router

**Middleware correto (Next.js + Supabase):**
```typescript
// middleware.ts
import { createServerClient } from '@supabase/ssr'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  const response = NextResponse.next()
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    { cookies: { /* ... */ } }
  )
  const { data: { user } } = await supabase.auth.getUser()

  const isProtectedRoute = request.nextUrl.pathname.startsWith('/dashboard') ||
    request.nextUrl.pathname.startsWith('/admin') ||
    request.nextUrl.pathname.startsWith('/profile')

  if (isProtectedRoute && !user) {
    return NextResponse.redirect(new URL('/login', request.url))
  }
  return response
}

export const config = {
  matcher: ['/dashboard/:path*', '/admin/:path*', '/profile/:path*']
}
```

**Verificação server-side em page.tsx (App Router):**
```typescript
// app/dashboard/page.tsx
import { createClient } from '@/lib/supabase/server' // @supabase/ssr (auth-helpers-nextjs está DEPRECADO)
import { redirect } from 'next/navigation'

export default async function DashboardPage() {
  const supabase = await createClient()
  // ✅ getUser() revalida o JWT no Auth server — NUNCA use getSession() aqui
  const { data: { user }, error } = await supabase.auth.getUser()
  if (error || !user) redirect('/login')
  // ...
}
```
> Regra: em qualquer código server-side (page, layout, Route Handler, Server Action), use `auth.getUser()`. `auth.getSession()` lê o cookie sem revalidar e aceita JWT expirado/revogado — é anti-padrão mesmo como exemplo.

---

### Supabase RLS — Correções Comuns

**Padrão correto de policy para dados do usuário:**
```sql
-- SELECT: usuário vê apenas seus próprios dados
CREATE POLICY "select_own_data" ON tabela
  FOR SELECT TO authenticated
  USING (auth.uid() = user_id);

-- INSERT: usuário só insere com seu próprio user_id
CREATE POLICY "insert_own_data" ON tabela
  FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = user_id);

-- UPDATE: usuário só atualiza seus próprios dados
CREATE POLICY "update_own_data" ON tabela
  FOR UPDATE TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- DELETE: usuário só deleta seus próprios dados
CREATE POLICY "delete_own_data" ON tabela
  FOR DELETE TO authenticated
  USING (auth.uid() = user_id);
```

**Verificar todas as tabelas de uma vez:**
```sql
SELECT
  t.tablename,
  t.rowsecurity,
  COUNT(p.policyname) as policy_count,
  STRING_AGG(p.policyname, ', ') as policies
FROM pg_tables t
LEFT JOIN pg_policies p ON t.tablename = p.tablename AND p.schemaname = 'public'
WHERE t.schemaname = 'public'
GROUP BY t.tablename, t.rowsecurity
ORDER BY t.rowsecurity ASC, t.tablename;
```

---

### Criação de usuário com senha temporária/padrão

**Checklist técnico:**
- [ ] Senha temporária gerada com CSPRNG (`crypto.randomBytes`), não `Math.random()` nem string fixa
- [ ] Comprimento/entropia equivalente a senha forte (≥ 16 bytes aleatórios em base64url)
- [ ] Flag "deve trocar senha" gravada em `app_metadata` (nunca `user_metadata`)
- [ ] Middleware/guard bloqueia toda rota exceto `/change-password`/`/logout` enquanto a flag estiver ativa — inclusive chamadas de API/Server Actions
- [ ] Flag limpa só no servidor, após confirmar nova senha definida
- [ ] Nenhum log grava o valor da senha temporária
- [ ] Se usa link de primeiro acesso: expira (≤ 24-48h) e é single-use

```bash
grep -rnE "Math\.random\(\)|Mudar123|Temp@123|Welcome123|senha.*padrão|DEFAULT_PASSWORD" \
  src/ app/ supabase/functions/ --include="*.ts" --include="*.tsx"
grep -rnE "console\.(log|info|debug)\(.*\b(temp|temporary|tempPassword|senha)\b" \
  src/ app/ supabase/functions/ --include="*.ts" --include="*.tsx" -i
```

**Payload de teste:**
1. Admin cria usuário com senha temporária. Login sucede, mas qualquer chamada subsequente (Server Action/Route Handler direto via fetch, ignorando UI) deve recusar até a troca:
   ```typescript
   const res = await fetch('/api/dashboard-data', { headers: { Authorization: `Bearer ${sessionWithTempPasswordFlag}` } })
   expect(res.status).toBe(403)
   ```
2. Após trocar, confirme flag `false` persistida no banco (não só na sessão em memória).
3. Tente reutilizar a senha temporária antiga — deve falhar.

```typescript
// Sanity check de entropia (10.000 gerações, sem colisão)
const passwords = Array.from({ length: 10000 }, () => generateTempPassword())
expect(new Set(passwords).size).toBe(10000)
```

---

## P1 — Alto {#p1}

### getSession() vs getUser() — aviso crítico

Este é um dos erros mais frequentes e perigosos em apps Supabase + Next.js:

```typescript
// ❌ INSEGURO: getSession() NÃO revalida o token no servidor
// Retorna a sessão do cookie sem verificar se ainda é válida
const { data: { session } } = await supabase.auth.getSession()
// session pode existir mesmo com JWT expirado ou revogado

// ✅ CORRETO: getUser() valida o JWT no servidor Auth antes de retornar
const { data: { user }, error } = await supabase.auth.getUser()
if (error || !user) {
  return NextResponse.json({ error: 'Não autorizado' }, { status: 401 })
}
```

**Onde verificar:**
- Todos os `app/api/` Route Handlers
- Todos os Server Actions (`'use server'`)
- Qualquer `getServerSideProps` ou page server component que lê dados protegidos

**Buscar no projeto:**
```bash
grep -rn "auth.getSession()" src/ app/ --include="*.ts" --include="*.tsx"
# Cada resultado é um candidato a substituir por getUser()
```

### CVE-2025-29927 — Middleware Next.js não é fronteira de segurança

O middleware do Next.js foi vulnerável ao CVE-2025-29927 que permitia bypass completo da autenticação via header `x-middleware-subrequest`. Mesmo com a versão corrigida, **o middleware não deve ser a única verificação de autenticação**.

Regra: sempre revalidar autenticação dentro de cada Route Handler e Server Action, independente do middleware.

```typescript
// ❌ INSEGURO: confia apenas no middleware para proteger
// app/api/dados-sensiveis/route.ts
export async function GET() {
  // Sem verificação de auth aqui — assume que o middleware já checou
  const dados = await db.query(...)
  return Response.json(dados)
}

// ✅ CORRETO: cada handler verifica independentemente
export async function GET() {
  const supabase = await createClient()
  const { data: { user }, error } = await supabase.auth.getUser()
  if (error || !user) return new Response('Unauthorized', { status: 401 })
  // Só aqui acessa dados
}
```

**Verificar versão do Next.js** (CVE-2025-29927 afeta versões anteriores a 14.2.25 / 15.2.3):
```bash
cat package.json | grep '"next"'
```

### JWT — Claims seguros vs. inseguros

**PERIGOSO — manipulável pelo usuário:**
```sql
-- user_metadata pode ser alterado pelo próprio usuário via supabase.auth.updateUser()
USING (auth.jwt()->'user_metadata'->>'role' = 'admin')
```

**SEGURO — só pode ser alterado pelo admin:**
```sql
-- app_metadata só pode ser alterado via service_role
USING (auth.jwt()->'app_metadata'->>'role' = 'admin')
```

**Verificar em Edge Functions:**
```typescript
// ERRADO — apenas decodifica sem verificar assinatura
import jwt from 'jsonwebtoken'
const decoded = jwt.decode(token) // NÃO valida assinatura!

// CORRETO — valida assinatura com Supabase
const { data: { user }, error } = await supabase.auth.getUser(token)
if (error || !user) return new Response('Unauthorized', { status: 401 })
```

---

### MFA — Implementação correta

**Policy que exige MFA (AAL2):**
```sql
-- Para tabelas com dados financeiros ou sensíveis
CREATE POLICY "require_mfa" ON tabela_financeira
  FOR ALL TO authenticated
  USING (
    (auth.jwt()->>'aal') = 'aal2'
    AND auth.uid() = user_id
  );
```

**Verificar AAL no frontend (TypeScript):**
```typescript
// ✅ Use getAuthenticatorAssuranceLevel — NÃO derive AAL de factors.length.
// user.factors lista fatores CADASTRADOS, não o nível de garantia da sessão atual.
// (Conta com MFA enrolado mas logada só por senha é AAL1, não AAL2.)
const checkMFA = async () => {
  const { data, error } = await supabase.auth.mfa.getAuthenticatorAssuranceLevel()
  if (error || !data) return
  // currentLevel = garantia da sessão agora; nextLevel = após desafio MFA bem-sucedido
  if (requiresMFA && data.currentLevel !== 'aal2') {
    router.push('/mfa-verify')
  }
}
```
> Para dados financeiros/sensíveis, combine com a policy server-side `auth.jwt()->>'aal' = 'aal2'` (acima). A checagem no cliente é só UX — a fronteira real é a policy.

---

### Sessão & Logout seguro

**Logout correto:**
```typescript
// CORRETO — invalida sessão no servidor
const handleLogout = async () => {
  await supabase.auth.signOut({ scope: 'global' }) // invalida TODAS as sessões
  router.push('/login')
}

// ERRADO — apenas limpa o cliente, token JWT ainda válido
localStorage.removeItem('supabase.auth.token')
```

**Configuração de cookies seguros (Next.js):**
```typescript
// Em next.config.ts ou middleware — garantir cookies HttpOnly
cookies: {
  set(name, value, options) {
    cookieStore.set({ name, value, ...options, httpOnly: true, secure: true, sameSite: 'strict' })
  }
}
```

---

### CORS — Edge Functions

**Configuração CORS restritiva:**
```typescript
// supabase/functions/_shared/cors.ts
const ALLOWED_ORIGINS = [
  'https://seudominio.com',
  'https://www.seudominio.com',
  ...(Deno.env.get('ENVIRONMENT') === 'development' ? ['http://localhost:3000'] : [])
]

export function corsHeaders(origin: string | null) {
  const allowed = origin && ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0]
  return {
    'Access-Control-Allow-Origin': allowed,
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
    'Vary': 'Origin'
  }
}
```

---

### Rate Limiting — Implementação

**Com Upstash Redis (recomendado para Vercel Edge):**
```typescript
// middleware.ts ou api/route.ts
import { Ratelimit } from "@upstash/ratelimit"
import { Redis } from "@upstash/redis"

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, "10 s"),
  analytics: true,
})

export async function rateLimitMiddleware(request: Request) {
  // ⚠️ NÃO use o x-forwarded-for do cliente (spoofável → bypass do limite e DoS de vítimas).
  // Na Vercel/Next, prefira o IP da plataforma (ex.: (request as NextRequest).ip) ou o header confiável do proxy.
  const ip = request.headers.get('x-real-ip')
    ?? request.headers.get('cf-connecting-ip')
    ?? '127.0.0.1'
  const { success, limit, reset, remaining } = await ratelimit.limit(`ratelimit_${ip}`)
  if (!success) {
    return new Response(JSON.stringify({ error: 'Too Many Requests' }), {
      status: 429,
      headers: {
        'X-RateLimit-Limit': limit.toString(),
        'X-RateLimit-Remaining': remaining.toString(),
        'X-RateLimit-Reset': new Date(reset).toISOString()
      }
    })
  }
}
```

**Supabase Auth Rate Limits (verificar no dashboard):**
- Settings → Auth → Rate Limits
- Signup: máximo 4/hora por IP (padrão conservador)
- OTP: máximo 30/hora
- Password recovery: máximo 3/hora

**Rate limiting por endpoint (limites diferentes por criticidade):**
```typescript
// Configurar limitadores separados por endpoint
const loginRatelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(5, "1 m"),   // login: 5 tentativas/minuto
  prefix: "ratelimit_login"
})

const searchRatelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(100, "1 m"),  // busca: 100/minuto
  prefix: "ratelimit_search"
})

// Endpoints de maior risco precisam de limites mais restritivos:
// POST /login, /signup, /reset-password → 5/min por IP
// POST /api/upload → 10/min por usuário
// GET /api/search → 100/min por IP
```

**Honeypots — rotas falsas para detectar scanners:**
```typescript
// app/api/admin-backup/route.ts — rota honeypot
// Qualquer acesso a esta rota é automaticamente suspeito
export async function GET(request: Request) {
  const ip = request.headers.get('x-real-ip') ?? request.headers.get('cf-connecting-ip') ?? 'unknown'
  // ⚠️ Não auto-bane por header spoofável — atacante pode fazer você banir IP de vítimas (DoS). Logue e alerte.
  console.warn(`[HONEYPOT] Acesso suspeito de IP: ${ip}`)
  // Retornar resposta plausível para não alertar o atacante
  return Response.json({ error: 'Unauthorized' }, { status: 401 })
}
```
Rotas honeypot úteis: `/api/admin-backup`, `/api/export-users`, `/.env`, `/api/debug`

---

### Input size limits — Prevenção de DoS via storage

Campos sem limite de tamanho permitem que atacantes injetem dados enormes que consomem armazenamento, processamento e memória.

**Auditoria rápida — campos sem .max():**
```bash
# Procurar schemas Zod sem .max() em campos de texto
grep -rn "z\.string()" src/ app/ --include="*.ts" --include="*.tsx" | grep -v "\.max("

# Procurar tabelas com colunas TEXT sem CHECK constraint
# (executar no SQL Editor do Supabase):
```
```sql
-- Listar colunas TEXT/VARCHAR sem constraints de tamanho:
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND data_type IN ('text', 'character varying')
  AND character_maximum_length IS NULL
ORDER BY table_name, column_name;
```

**Correção — Zod no servidor (primeira linha de defesa):**
```typescript
const ProfileSchema = z.object({
  name:        z.string().min(1).max(100).trim(),
  username:    z.string().min(3).max(30).regex(/^[a-z0-9_-]+$/i),
  bio:         z.string().max(500).optional(),
  website:     z.string().url().max(200).optional(),
  location:    z.string().max(100).optional(),
})

const MessageSchema = z.object({
  content:     z.string().min(1).max(2000),
  subject:     z.string().max(200).optional(),
})

const CommentSchema = z.object({
  body:        z.string().min(1).max(1000),
})

// Referência rápida de limites recomendados:
// name/title: max 200
// bio/description: max 500
// message/comment: max 2000
// email: max 254 (RFC 5321)
// slug/username: max 100
// URL: max 2048
// address line: max 200
```

**Correção — CHECK constraints no banco (segunda linha de defesa):**
```sql
-- Adicionar constraints para os campos mais críticos
ALTER TABLE public.profiles
  ADD CONSTRAINT name_max_length CHECK (length(name) <= 100),
  ADD CONSTRAINT bio_max_length CHECK (length(bio) <= 500);

ALTER TABLE public.messages
  ADD CONSTRAINT content_max_length CHECK (length(content) <= 2000);

ALTER TABLE public.posts
  ADD CONSTRAINT title_max_length CHECK (length(title) <= 200),
  ADD CONSTRAINT body_max_length CHECK (length(body) <= 50000);
```

---

### Testes automatizados de segurança

**Verificar cobertura existente:**
```bash
# Procurar arquivos de teste
find . -name "*.test.ts" -o -name "*.spec.ts" -o -name "*.test.tsx" \
  | grep -v node_modules

# Verificar se há testes de autenticação/autorização
grep -rn "unauthorized\|forbidden\|401\|403\|idor\|access.*denied" \
  --include="*.test.*" --include="*.spec.*" .
```

**Template de testes de segurança (Vitest/Jest):**
```typescript
// __tests__/security/idor.test.ts
import { describe, it, expect, beforeAll } from 'vitest'

describe('IDOR Prevention', () => {
  let userAToken: string
  let userBToken: string
  let userBResourceId: string

  beforeAll(async () => {
    // Setup: criar dois usuários e um recurso do usuário B
    userAToken = await signIn('user-a@test.com', 'password')
    userBToken = await signIn('user-b@test.com', 'password')
    const resource = await createResource(userBToken, { title: 'User B resource' })
    userBResourceId = resource.id
  })

  it('should not allow user A to read user B resource', async () => {
    const res = await fetch(`/api/resources/${userBResourceId}`, {
      headers: { Authorization: `Bearer ${userAToken}` }
    })
    // RLS NÃO devolve 403: leitura bloqueada retorna 200 com [] / count 0.
    const body = await res.json().catch(() => null)
    const leaked = JSON.stringify(body)
    expect(leaked).not.toContain(userBResourceId)
    expect(leaked).not.toContain('User B resource')
  })

  it('should not allow user A to update user B resource', async () => {
    const res = await fetch(`/api/resources/${userBResourceId}`, {
      method: 'PUT',
      headers: { Authorization: `Bearer ${userAToken}` },
      body: JSON.stringify({ title: 'Hijacked' })
    })
    // UPDATE bloqueado por RLS afeta 0 linhas (200, count:0) — confirme lendo de volta
    const check = await fetch(`/api/resources/${userBResourceId}`, {
      headers: { Authorization: `Bearer ${userBToken}` }
    })
    const after = await check.json()
    expect(JSON.stringify(after)).not.toContain('Hijacked')
  })

  it('should not allow user A to delete user B resource', async () => {
    await fetch(`/api/resources/${userBResourceId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${userAToken}` }
    })
    // DELETE bloqueado por RLS afeta 0 linhas — o recurso do B ainda existe
    const check = await fetch(`/api/resources/${userBResourceId}`, {
      headers: { Authorization: `Bearer ${userBToken}` }
    })
    expect(check.status).toBe(200)
  })
})

describe('Auth Protection', () => {
  it('should reject requests without token', async () => {
    const res = await fetch('/api/protected-endpoint')
    expect(res.status).toBe(401)
  })

  it('should reject requests with invalid token', async () => {
    const res = await fetch('/api/protected-endpoint', {
      headers: { Authorization: 'Bearer invalid-token' }
    })
    expect(res.status).toBe(401)
  })
})

describe('Input Validation', () => {
  it('should reject oversized input', async () => {
    const token = await signIn('user@test.com', 'password')
    const res = await fetch('/api/profile', {
      method: 'PUT',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ bio: 'a'.repeat(10000) }) // muito maior que o limite
    })
    expect(res.status).toBe(400)
  })

  it('should reject XSS in input fields', async () => {
    const token = await signIn('user@test.com', 'password')
    const res = await fetch('/api/posts', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: '<script>alert(1)</script>', body: 'test' })
    })
    // Deve ou rejeitar (400) ou sanitizar — nunca armazenar o script bruto
    if (res.ok) {
      const post = await res.json()
      expect(post.title).not.toContain('<script>')
    } else {
      expect(res.status).toBe(400)
    }
  })
})
```

---

### XSS — Sanitização

**Instalação:**
```bash
npm install dompurify
npm install -D @types/dompurify
```

**Uso correto:**
```typescript
import DOMPurify from 'dompurify'

// Para conteúdo HTML gerado pelo usuário
const SafeContent = ({ html }: { html: string }) => (
  <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'b', 'i', 'em', 'strong', 'a', 'ul', 'ol', 'li'],
    ALLOWED_ATTR: ['href', 'target', 'rel'],
    FORCE_BODY: true
  }) }} />
)
```

**Validação com Zod (para inputs de API):**
```typescript
import { z } from 'zod'

const UserInputSchema = z.object({
  name: z.string().min(1).max(100).trim(),
  email: z.string().email(),
  bio: z.string().max(500).optional(),
  // NUNCA aceitar: role, plan, is_admin, price via input do usuário
})

// Em Edge Function ou API Route:
const result = UserInputSchema.safeParse(req.body)
if (!result.success) return new Response('Invalid input', { status: 400 })
```

---

### .or() PostgREST Injection

O método `.or()` do supabase-js aceita strings de query raw. Se input do usuário for interpolado diretamente, o filtro pode ser manipulado:

```typescript
// ❌ PERIGOSO: account_id vem diretamente do request body
const { data } = await supabase
  .from('pedidos')
  .select()
  .or(`tenant_id.is.null,tenant_id.eq.${account_id}`)
// Se account_id = '0,tenant_id.gte.1' → filtro manipulado, vê dados de todos

// ✅ SEGURO: validar que é um UUID antes de usar
import { z } from 'zod'
const accountIdSchema = z.string().uuid()
const validId = accountIdSchema.parse(account_id) // lança se não for UUID
```

Buscar no projeto:
```bash
grep -rn "\.or(\`" src/ app/ --include="*.ts" --include="*.tsx"
# Cada backtick dentro de .or() é suspeito — pode ser interpolação
```

### Realtime — canais privados e RLS em realtime.messages

**Dois mecanismos distintos:**
- `Broadcast` e `Presence`: usam RLS na tabela `realtime.messages` + `config: { private: true }`
- `Postgres Changes`: usam RLS da **tabela de origem** (não precisa de `private: true`)

**Configurar Broadcast seguro:**

```sql
-- 1. No Dashboard: Realtime → Settings → desabilitar "Allow public access"

-- 2. Política para receber broadcasts em uma sala
CREATE POLICY "Membros recebem mensagens da sala"
  ON realtime.messages FOR SELECT TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM salas_usuarios
      WHERE user_id = (SELECT auth.uid())
      AND topico_sala = (SELECT realtime.topic())
    )
    AND realtime.messages.extension IN ('broadcast')
  );

-- 3. Política para enviar broadcasts
CREATE POLICY "Membros enviam mensagens da sala"
  ON realtime.messages FOR INSERT TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM salas_usuarios
      WHERE user_id = (SELECT auth.uid())
      AND topico_sala = (SELECT realtime.topic())
    )
    AND realtime.messages.extension IN ('broadcast')
  );
```

**Client-side — obrigatório usar `private: true`:**
```typescript
const canal = supabase.channel('sala-123', {
  config: { private: true }, // SEM isso, a autorização NÃO funciona
})
```

**Verificar no projeto:**
```bash
# Buscar channels sem private: true
grep -rn "supabase.channel(" src/ app/ --include="*.ts" --include="*.tsx" -A 3 | grep -v "private: true"
```

### Storage — URLs assinadas para buckets privados

Nunca exponha URLs diretas de arquivos privados. Use URLs temporárias:

```typescript
// Gerar URL temporária (válida por 5 minutos)
const { data, error } = await supabase.storage
  .from('arquivos-usuario')
  .createSignedUrl('pasta/arquivo.pdf', 300) // 300 segundos = 5 min

// Para downloads em lote
const { data } = await supabase.storage
  .from('arquivos-usuario')
  .createSignedUrls(['arquivo1.pdf', 'arquivo2.pdf'], 300)
```

**Política de path traversal:**
```sql
-- Prevenir acesso fora da pasta do usuário
CREATE POLICY "Prevenir path traversal"
  ON storage.objects FOR INSERT TO authenticated
  WITH CHECK (
    bucket_id = 'arquivos-usuario' AND
    (storage.foldername(name))[1] = (SELECT auth.jwt() ->> 'sub') AND
    name NOT LIKE '%..%'
  );
```

---

### Recuperação de senha — token

**Três propriedades obrigatórias do token:** (1) entropia ≥128 bits CSPRNG, (2) expiração 15-60min, (3) uso único — invalidar após troca bem-sucedida E invalidar tokens anteriores ao emitir um novo.

```sql
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'password_resets' AND table_schema = 'public';
SELECT id, email FROM public.password_resets WHERE expires_at IS NULL;
```
```bash
grep -rn "password_resets\|reset_token" src/ app/ supabase/functions/ --include="*.ts" | grep -v "token_hash\|createHash"
```
Se o token é comparado direto (`WHERE token = $1`) em vez de por hash, vazamento de banco expõe tokens ativos — sempre armazenar `sha256(token)`.

**Referrer leakage — checklist:**
- [ ] `Referrer-Policy: no-referrer` nas rotas `/reset-password`, `/update-password`, `/forgot-password`
- [ ] Nenhum script de terceiro nessas páginas
- [ ] Error tracker global (Sentry) faz scrub de `window.location.href` antes de reportar

```bash
grep -rln "gtag\|analytics\|hotjar\|clarity\|intercom\|drift\|fullstory\|sentry" \
  src/app/reset-password src/app/update-password app/reset-password app/update-password \
  pages/reset-password pages/update-password 2>/dev/null
```

**Payload de teste:** solicitar reset, aguardar expiração e confirmar rejeição; usar token uma vez e tentar reutilizar; solicitar dois resets seguidos e confirmar que o primeiro token foi invalidado; checar header Referrer de requests de terceiro na página de reset.

### Login via código OTP

O ponto que mais escapa de auditorias superficiais: **rate-limit na verificação**, não só na geração.

**Checklist técnico:**
- [ ] Código ≥6 dígitos, CSPRNG (`crypto.randomInt`)
- [ ] Expiração 5-10min
- [ ] Uso único — invalidado após verificação bem-sucedida
- [ ] Reenvio invalida código anterior
- [ ] Rate-limit na verificação — máx 5 tentativas antes de invalidar
- [ ] Rate-limit também na geração/reenvio (independente do de verificação)
- [ ] Código nunca retornado na resposta/headers/logs
- [ ] Comparação contra hash armazenado

```bash
grep -rnE "Math\.random\(\).{0,40}(otp|code|OTP)" src/ app/ supabase/functions/ --include="*.ts" --include="*.tsx" -i
grep -rl "verifyOtp\|verify.*[Oo][Tt][Pp]\|checkOtp\|validateCode" src/ app/ supabase/functions/ \
  --include="*.ts" --include="*.tsx" | xargs grep -L "attempts\|rateLimit\|ratelimit\|lockout\|max.*tries" 2>/dev/null
grep -rnE "(debug_otp|return.*\{[^}]*\botp\b|json\(\{[^}]*\bcode\b.*otp)" \
  src/ app/ supabase/functions/ --include="*.ts" --include="*.tsx" -i
```

**Payload de teste — brute-force do endpoint de verificação:**
```typescript
async function bruteForceOtp(email: string) {
  for (let i = 0; i <= 20; i++) {
    const code = i.toString().padStart(6, '0')
    const res = await fetch('/api/auth/verify-otp', { method: 'POST', body: JSON.stringify({ email, code }) })
    if (res.status === 429 || (await res.json()).error?.includes('Muitas tentativas')) {
      console.log(`Bloqueado após ${i + 1} tentativas — OK`); return
    }
  }
  console.log('⚠️ Nenhum bloqueio detectado após 21 tentativas — VULNERÁVEL')
}
```
Se o teste completa sem bloqueio, é achado P0 confirmado.

---

## P2 — Médio {#p2}

### Upload de Arquivos — Magic Bytes

```typescript
// Validação por magic bytes (mais segura que extensão)
const MAGIC_BYTES: Record<string, number[]> = {
  'image/jpeg': [0xFF, 0xD8, 0xFF],
  'image/png': [0x89, 0x50, 0x4E, 0x47],
  'image/webp': [0x52, 0x49, 0x46, 0x46],
  'application/pdf': [0x25, 0x50, 0x44, 0x46],
}

async function validateFileType(file: File, allowedTypes: string[]): Promise<boolean> {
  const buffer = await file.arrayBuffer()
  const bytes = new Uint8Array(buffer.slice(0, 8))
  return allowedTypes.some(type => {
    const magic = MAGIC_BYTES[type]
    return magic && magic.every((byte, i) => bytes[i] === byte)
  })
}

// Nome seguro para evitar path traversal
const safeFileName = `${crypto.randomUUID()}.${file.name.split('.').pop()?.toLowerCase()}`
```

---

### console.log — Remoção em produção

**Next.js (next.config.ts):**
```typescript
const nextConfig = {
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production' ? { exclude: ['error'] } : false,
  },
  productionBrowserSourceMaps: false,
}
```

**Vite (vite.config.ts):**
```typescript
export default defineConfig({
  build: {
    sourcemap: false, // nunca em produção
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      }
    }
  }
})
```

---

### LGPD — Deleção de dados

**Hard delete (correto para LGPD):**
```sql
-- Função para deletar todos os dados do usuário
CREATE OR REPLACE FUNCTION delete_user_data(p_user_id UUID)
RETURNS void AS $$
BEGIN
  DELETE FROM user_profiles WHERE user_id = p_user_id;
  DELETE FROM user_orders WHERE user_id = p_user_id;
  DELETE FROM user_uploads WHERE user_id = p_user_id;
  -- Deletar arquivos do Storage
  -- Deletar via auth.admin em Edge Function separada
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = '';
```

**ERRADO — soft delete não atende LGPD:**
```sql
UPDATE users SET deleted_at = NOW() WHERE id = user_id -- dados ainda existem
```

---

### Race Conditions — Cenários concretos de lógica de negócio

Esta é a categoria onde a IA mais falha em vibe-coding. Pense em fluxos absurdos que combinam ações legítimas:

**Cenários a investigar no projeto:**

| Cenário | Pergunta a fazer |
|---------|-----------------|
| Compra + reembolso + comissão | Ao solicitar reembolso, a comissão do afiliado é revertida? |
| Duplo clique em "Comprar" | O usuário pode comprar duas vezes simultaneamente? |
| Cupom de desconto | Pode usar o mesmo cupom em duas sessões paralelas? |
| Saldo/créditos | Pode debitar mais do que tem se duas requisições chegam ao mesmo tempo? |
| Bônus de indicação | Pode indicar a si mesmo via e-mail alternativo? |
| Trial gratuito | Pode criar conta, cancelar, recriar e ter novo trial? |
| Webhook de pagamento | O que acontece se o webhook chegar duas vezes (retentativa)? |

**Padrão vulnerável — janela de race condition:**
```typescript
// ❌ Duas operações separadas — atacante pode explorar a janela entre elas
const balance = await getBalance(userId)           // query 1
if (balance >= amount) {
  await deductBalance(userId, amount)              // query 2 — race condition aqui
  await creditSeller(sellerId, amount)             // query 3
}
// Um atacante com duas requisições simultâneas pode executar ambas
// quando o saldo ainda não foi debitado
```

**Padrão seguro — operação atômica COM autorização (não confie no chamador):**
```sql
-- Pré-requisitos OBRIGATÓRIOS (sem eles o snippet falha ou fica inseguro):
-- ALTER TABLE transactions ADD CONSTRAINT uq_idem UNIQUE (idempotency_key);
-- REVOKE EXECUTE ON FUNCTION public.process_purchase(uuid,uuid,numeric,text) FROM anon, authenticated;
-- GRANT EXECUTE ON FUNCTION public.process_purchase(uuid,uuid,numeric,text) TO <server_role>;

CREATE OR REPLACE FUNCTION public.process_purchase(
  p_buyer_id uuid,           -- ignorado: derivado de auth.uid()
  p_seller_id uuid,
  p_amount numeric,
  p_idempotency_key text
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
  v_buyer uuid := auth.uid();  -- comprador é SEMPRE o usuário autenticado
BEGIN
  IF v_buyer IS NULL THEN
    RETURN jsonb_build_object('status', 'error', 'message', 'Não autenticado');
  END IF;
  IF p_amount IS NULL OR p_amount <= 0 THEN
    RETURN jsonb_build_object('status', 'error', 'message', 'Valor inválido');
  END IF;

  -- Prevenir duplicatas via idempotency key (exige UNIQUE acima)
  INSERT INTO public.transactions (idempotency_key, buyer_id, seller_id, amount, status)
  VALUES (p_idempotency_key, v_buyer, p_seller_id, p_amount, 'processing')
  ON CONFLICT (idempotency_key) DO NOTHING;

  IF NOT FOUND THEN
    RETURN jsonb_build_object('status', 'duplicate', 'message', 'Transação já processada');
  END IF;

  -- Debitar e verificar saldo na mesma operação atômica (do comprador autenticado)
  UPDATE public.wallets
  SET balance = balance - p_amount
  WHERE user_id = v_buyer AND balance >= p_amount;

  IF NOT FOUND THEN
    DELETE FROM public.transactions WHERE idempotency_key = p_idempotency_key;
    RETURN jsonb_build_object('status', 'error', 'message', 'Saldo insuficiente');
  END IF;

  UPDATE public.wallets SET balance = balance + p_amount WHERE user_id = p_seller_id;
  UPDATE public.transactions SET status = 'completed' WHERE idempotency_key = p_idempotency_key;

  RETURN jsonb_build_object('status', 'success');
END;
$$;
```
> Por quê: sem `SECURITY DEFINER` + `auth.uid()` + `amount > 0` + `REVOKE`, qualquer `authenticated` chamaria `rpc('process_purchase', { buyer: '<vítima>', seller: '<eu>', amount: 99999 })` — e valor negativo viraria auto-crédito. Função financeira nunca é pública.

**Verificar no código:**
```bash
# Operações financeiras fora de transactions/RPCs
grep -rn "supabase\.from.*update\|supabase\.from.*insert" \
  src/ app/ --include="*.ts" --include="*.tsx" | grep -i "balance\|credit\|debit\|payment\|wallet\|bonus"

# Verificar se há chamadas a .rpc() para operações financeiras (bom sinal)
grep -rn "\.rpc(" src/ app/ --include="*.ts" --include="*.tsx"
```

**Webhooks — verificar assinatura ANTES da idempotência (P0):**

Idempotência só impede **replay** de um `event_id` já visto — não impede evento **forjado**. Sem verificar assinatura, qualquer um POSTa um `checkout.session.completed` e credita compra/plano sem pagar. Valide primeiro.

```typescript
// Stripe — verificação de assinatura com o corpo CRU (raw body)
import Stripe from 'stripe'
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

export async function POST(req: Request) {
  const sig = req.headers.get('stripe-signature')
  const rawBody = await req.text() // corpo cru, NÃO req.json()
  let event: Stripe.Event
  try {
    event = stripe.webhooks.constructEvent(rawBody, sig!, process.env.STRIPE_WEBHOOK_SECRET!)
  } catch {
    return new Response('Invalid signature', { status: 400 }) // rejeita forjado
  }

  // Idempotência ATÔMICA (não check-then-act): UNIQUE(event_id) + ON CONFLICT
  const { data, error } = await supabase
    .from('processed_webhooks')
    .insert({ event_id: event.id, event_type: event.type })
    .select()
    .single()
  // Se já existia (unique violation), outra entrega já processou
  if (error?.code === '23505') return Response.json({ status: 'already_processed' })
  if (error) return new Response('retry', { status: 500 })

  await supabase.rpc('process_payment_event', {
    event_id: event.id, event_type: event.type, payload: event.data
  })
  return Response.json({ status: 'ok' })
}
```

Equivalentes: Svix/`standard-webhooks` (`wh.verify(rawBody, headers, secret)`), GitHub (`X-Hub-Signature-256` com HMAC-SHA256 + `crypto.timingSafeEqual`), Supabase Database Webhooks (HMAC no header). Regra: **assinatura → depois** idempotência atômica (`INSERT … ON CONFLICT` com `UNIQUE(event_id)`), nunca `select`→`insert` (TOCTOU) nem `new Set()` em serverless (cada cold start é vazio).

---

### Password hashing seguro

Se o projeto implementa autenticação própria (não usa Supabase Auth), o hashing é o controle mais crítico.

**Algoritmos recomendados (ordem de preferência):**

| Algoritmo | Salt automático | Resistência a GPU/ASIC | Recomendação |
|-----------|----------------|----------------------|--------------|
| Argon2id | Sim | Alta | **OWASP 2023 recommendation** |
| bcrypt | Sim | Média-alta | Custo mínimo 12 |
| scrypt | Sim | Média | Boa alternativa |
| PBKDF2 | Sim | Média | Iterações ≥ 600.000 |
| SHA-256/SHA-512 | Não | Baixa | **Inaceitável para senhas** |
| MD5/SHA-1 | Não | Muito baixa | **Inaceitável** |

**Exemplo com Argon2 (Node.js):**

```typescript
import { hash, verify } from 'argon2'

async function register(email: string, password: string) {
  const passwordHash = await hash(password, {
    type: 2,            // argon2id
    memoryCost: 19456,  // ~19 MiB — mínimo OWASP 2023
    timeCost: 2,
    parallelism: 1,
  }) // salt automático
  await db.users.insert({ email, password_hash: passwordHash })
}

async function login(email: string, password: string) {
  const user = await db.users.findOne({ email })
  if (!user) {
    await verify(DUMMY_HASH, password) // prevenir timing attack
    return { error: 'Credenciais inválidas' }
  }
  const valid = await verify(user.password_hash, password)
  if (!valid) return { error: 'Credenciais inválidas' }
  return { user }
}
```

**Buscar no projeto:**
```bash
grep -rnE "(md5|sha1|sha256|bcrypt|argon2|pbkdf2|hashPassword|compare)" \
  src/ app/ --include="*.ts" --include="*.tsx"
```

---

### Error handling seguro — fail-safe e não exposição

OWASP Top 10 2025 introduziu **A10: Mishandling of Exceptional Conditions**. Aplicações devem falhar de forma segura (fail-safe closed) e nunca expor detalhes internos.

**Padrões perigosos:**
```typescript
// ❌ Expor stack trace e mensagens internas
return Response.json({ error: err.message, stack: err.stack }, { status: 500 })

// ❌ Fail-open: se não conseguir verificar auth, permite
if (user?.role === 'admin') {
  // ação privilegiada
}
// sem else → não-admin passa silenciosamente se user for null
```

**Padrão seguro:**
```typescript
// ✅ Genérico para cliente, detalhado no log
console.error('[UNEXPECTED_ERROR]', err)
return Response.json({ error: 'Internal server error' }, { status: 500 })

// ✅ Fail-safe: nega por padrão
const { data: { user } } = await supabase.auth.getUser()
if (!user) {
  return Response.json({ error: 'Unauthorized' }, { status: 401 })
}
const isAdmin = user.app_metadata?.role === 'admin'
if (!isAdmin) {
  return Response.json({ error: 'Forbidden' }, { status: 403 })
}
```

**Verificar:**
```bash
grep -rn "error\.stack\|error\.message\|JSON\.stringify(error" \
  src/ app/ --include="*.ts" --include="*.tsx"
```

---

### Supply chain security

OWASP Top 10 2025 — **A03: Software Supply Chain Failures**.

**Checklist:**
- [ ] Lockfile commitado (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`)
- [ ] CI usa `npm ci` / `yarn install --frozen-lockfile` / `pnpm install --frozen-lockfile`
- [ ] Versões de dependências pinadas no `package.json` (evitar `^`/`~` para pacotes críticos)
- [ ] `.npmrc` com `engine-strict=true`
- [ ] Revisão de scripts `postinstall` suspeitos
- [ ] Dependabot/Renovate configurado para alertas de segurança

**Verificar postinstall scripts:**
```bash
grep -rn "postinstall\|preinstall" node_modules/*/package.json 2>/dev/null | head -20
```

**GitHub Actions seguro:**
```yaml
- name: Install dependencies
  run: npm ci  # nunca npm install em CI

- name: Audit
  run: npm audit --audit-level=high --production
```

---

### Brute force protection e account lockout

Além de rate limiting por IP, proteja contas individuais contra brute force direcionado.

**Com Supabase Auth:**
- Habilite Attack Protection + CAPTCHA (hCaptcha/Turnstile)
- Configure rate limits conservadores no Dashboard

**Com auth customizada:**
```sql
CREATE TABLE IF NOT EXISTS public.auth_attempts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT NOT NULL,
  ip INET,
  attempted_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_auth_attempts_email ON public.auth_attempts(email);
```

```typescript
async function checkLockout(email: string, ip: string): Promise<boolean> {
  const { count } = await supabase
    .from('auth_attempts')
    .select('*', { count: 'exact', head: true })
    .eq('email', email)
    .gt('attempted_at', new Date(Date.now() - 15 * 60 * 1000).toISOString())
  return (count ?? 0) >= 5
}
```

---

### LGPD — checklist técnico completo

**Direitos do titular (art. 18):**

1. **Confirmação e acesso** — endpoint `/api/me/data` retornando todos os dados pessoais
2. **Correção** — formulário de edição de perfil
3. **Anonimização, bloqueio ou eliminação** — rotina de hard delete ou anonimização irreversível
4. **Portabilidade** — exportação em JSON/CSV estruturado
5. **Informação sobre compartilhamento** — log de terceiros que receberam dados
6. **Revogação de consentimento** — tabela de consentimentos com `revoked_at`
7. **Oposição** — configurações de privacidade
8. **Revisão de decisões automatizadas** — fluxo de appeal humano

**Princípios técnicos:**
- **Minimização**: revise colunas `cpf`, `rg`, `phone`, `address`, `birth_date`, etc.
- **Finalidade**: documente por que cada dado é coletado
- **Retenção**: elimine automaticamente após o prazo necessário
- **Consentimento**: granular, claro, registrado e revogável
- **Segurança**: criptografia, RLS, MFA, logs de acesso
- **Transparência**: política de privacidade acessível e atualizada
- **Notificação de incidentes**: rotina para ANPD e titulares em até **3 dias úteis** (6 para agente de pequeno porte) a partir do conhecimento — Res. CD/ANPD 15/2024. ⚠️ Não confundir com os "72h" do GDPR.

**Hard delete seguro:**
```sql
CREATE OR REPLACE FUNCTION delete_user_data(p_user_id UUID)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
  DELETE FROM public.profiles WHERE user_id = p_user_id;
  DELETE FROM public.orders WHERE user_id = p_user_id;
  DELETE FROM public.activity_logs WHERE user_id = p_user_id;
  -- Edge Function separada para deletar arquivos do Storage
  -- Edge Function separada para deletar auth.users via service_role
END;
$$;
```

**Sentry sem PII:**
```typescript
Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  beforeSend(event) {
    if (event.user) {
      event.user = { id: event.user.id } // só mantém ID anonimizado
    }
    return event
  }
})
```

---

### PII detection e data classification

**Colunas típicas de PII:**
- Identificação: `name`, `full_name`, `email`, `cpf`, `rg`, `passport`, `document`
- Contato: `phone`, `phone_number`, `address`, `zip_code`
- Biográficos: `birth_date`, `age`, `gender`
- Financeiros: `card_number`, `bank_account`, `income`
- Sensíveis (LGPD art. 5º, II): `health`, `biometrics`, `religion`, `political`, `sexual_orientation`

**Query de mapeamento:**
```sql
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND column_name IN (
    'email', 'cpf', 'phone', 'phone_number', 'address', 'document',
    'passport', 'rg', 'birth_date', 'name', 'full_name', 'card_number'
  )
ORDER BY table_name, column_name;
```

**Classificação sugerida:**
- Público: dados que já são públicos
- Interno: dados operacionais não pessoais
- Confidencial: dados pessoais não sensíveis
- Sensível: dados sensíveis da LGPD

---

### Backup e disaster recovery

**Checklist:**
- [ ] Backups automáticos habilitados no Supabase Dashboard
- [ ] Backups testados periodicamente (restore em ambiente isolado)
- [ ] RTO e RPO documentados
- [ ] Backups criptografados em repouso e em trânsito
- [ ] Cópia off-site ou em região secundária para dados críticos
- [ ] Procedimento documento de recovery

**RTO/RPO exemplo:**
| Sistema | RTO | RPO |
|---------|-----|-----|
| Auth | 1h | 0 (sincrono) |
| Dados transacionais | 4h | 15 min |
| Logs/analytics | 24h | 1h |

---

## Ferramentas complementares {#ferramentas}

| Ferramenta | Uso | Como instalar/acessar |
|------------|-----|----------------------|
| `npm audit` | Vulnerabilidades em deps | `npm audit --audit-level=moderate` |
| Supabase Security Advisor | Scan automático de RLS | Dashboard → Database → Security Advisor |
| DOMPurify | Sanitização HTML | `npm install dompurify` |
| Zod | Validação de schema | `npm install zod` |
| Upstash Ratelimit | Rate limiting Edge | `npm install @upstash/ratelimit @upstash/redis` |
| GitLeaks | Detecta secrets em commits | `brew install gitleaks && gitleaks detect` |
| OWASP ZAP | Scan dinâmico de vulnerabilidades | zaproxy.org |
| Sentry | Error tracking sem source maps expostos | sentry.io |

### Supabase Security Advisor

Acessar em: Dashboard → Database → Security Advisor

Verifica automaticamente:
- Tabelas sem RLS
- Policies com USING (true)
- Functions SECURITY DEFINER sem search_path
- Extensions perigosas expostas

### Comandos úteis de auditoria rápida

```bash
# Buscar secrets hardcoded
grep -rE "(sk_live|sk_test|SERVICE_ROLE|eyJ[A-Za-z0-9]{40,})" src/ --include="*.ts" --include="*.tsx"

# Buscar dangerouslySetInnerHTML sem DOMPurify
grep -rn "dangerouslySetInnerHTML" src/ --include="*.tsx"

# Buscar console.log no código de produção
grep -rn "console\.\(log\|debug\|info\)" src/ --include="*.ts" --include="*.tsx"

# Buscar select * no Supabase (ERE; grupo balanceado)
grep -rnE "\.select\(\s*['\"]\*['\"]" src/ --include="*.ts" --include="*.tsx"

# Buscar localStorage com tokens
grep -rn "localStorage\." src/ --include="*.ts" --include="*.tsx"

# Buscar jwt.decode sem verify
grep -rn "jwt\.decode\b" src/ --include="*.ts"
```
