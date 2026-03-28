# Detalhes de Auditoria por Categoria

Referência completa com SQL queries, padrões de código e exemplos de correção para cada categoria do security-auditor.

## Índice
- [Seções P0 — Crítico](#p0)
- [Seções P1 — Alto](#p1)
- [Seções P2 — Médio](#p2)
- [Ferramentas complementares](#ferramentas)

> **v1.6:** Adicionadas seções — Enumeração de usuários, Input size limits, Rate limiting honeypots, Race conditions (cenários concretos), Upload (IP trackers), Testes de segurança TDD

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
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

export default async function DashboardPage() {
  const supabase = createServerComponentClient({ cookies })
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) redirect('/login')
  // ...
}
```

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
const checkMFA = async () => {
  const { data: { session } } = await supabase.auth.getSession()
  const aal = session?.user?.factors?.length > 0 ? 'aal2' : 'aal1'
  if (aal !== 'aal2' && requiresMFA) {
    router.push('/mfa-verify')
  }
}
```

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
  const ip = request.headers.get('x-forwarded-for') ?? '127.0.0.1'
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
  const ip = request.headers.get('x-forwarded-for') ?? 'unknown'
  // Log e bloquear o IP no Redis por 24h
  await redis.set(`honeypot_blocked_${ip}`, true, { ex: 86400 })
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
    expect(res.status).toBe(403)
  })

  it('should not allow user A to update user B resource', async () => {
    const res = await fetch(`/api/resources/${userBResourceId}`, {
      method: 'PUT',
      headers: { Authorization: `Bearer ${userAToken}` },
      body: JSON.stringify({ title: 'Hijacked' })
    })
    expect(res.status).toBe(403)
  })

  it('should not allow user A to delete user B resource', async () => {
    const res = await fetch(`/api/resources/${userBResourceId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${userAToken}` }
    })
    expect(res.status).toBe(403)
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
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;
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

**Padrão seguro — operação atômica:**
```sql
-- Tudo em uma única transaction com verificação e ação combinadas
CREATE OR REPLACE FUNCTION process_purchase(
  p_buyer_id uuid,
  p_seller_id uuid,
  p_amount numeric,
  p_idempotency_key text
)
RETURNS jsonb
LANGUAGE plpgsql AS $$
DECLARE
  v_balance numeric;
BEGIN
  -- Prevenir duplicatas via idempotency key
  INSERT INTO transactions (idempotency_key, buyer_id, seller_id, amount, status)
  VALUES (p_idempotency_key, p_buyer_id, p_seller_id, p_amount, 'processing')
  ON CONFLICT (idempotency_key) DO NOTHING;

  IF NOT FOUND THEN
    RETURN jsonb_build_object('status', 'duplicate', 'message', 'Transação já processada');
  END IF;

  -- Debitar e verificar saldo na mesma operação atômica
  UPDATE wallets
  SET balance = balance - p_amount
  WHERE user_id = p_buyer_id AND balance >= p_amount;

  IF NOT FOUND THEN
    -- Reverter a transaction marcada como processing
    DELETE FROM transactions WHERE idempotency_key = p_idempotency_key;
    RETURN jsonb_build_object('status', 'error', 'message', 'Saldo insuficiente');
  END IF;

  -- Creditar vendedor
  UPDATE wallets SET balance = balance + p_amount WHERE user_id = p_seller_id;

  -- Marcar como concluída
  UPDATE transactions SET status = 'completed' WHERE idempotency_key = p_idempotency_key;

  RETURN jsonb_build_object('status', 'success');
END;
$$;
```

**Verificar no código:**
```bash
# Operações financeiras fora de transactions/RPCs
grep -rn "supabase\.from.*update\|supabase\.from.*insert" \
  src/ app/ --include="*.ts" --include="*.tsx" | grep -i "balance\|credit\|debit\|payment\|wallet\|bonus"

# Verificar se há chamadas a .rpc() para operações financeiras (bom sinal)
grep -rn "\.rpc(" src/ app/ --include="*.ts" --include="*.tsx"
```

**Idempotency em webhooks (Stripe/pagamentos):**
```typescript
// Edge Function para webhook de pagamento
const processedEvents = new Set() // ou Redis em produção

export async function POST(req: Request) {
  const event = await parseWebhook(req)

  // Verificar se já processamos este evento
  const { data: existing } = await supabase
    .from('processed_webhooks')
    .select('id')
    .eq('event_id', event.id)
    .single()

  if (existing) return Response.json({ status: 'already_processed' })

  // Processar e registrar atomicamente
  await supabase.rpc('process_payment_event', {
    event_id: event.id,
    event_type: event.type,
    payload: event.data
  })
}
```

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

# Buscar select * no Supabase
grep -rn "\.select\(['\"]\\*['\"]" src/ --include="*.ts" --include="*.tsx"

# Buscar localStorage com tokens
grep -rn "localStorage\." src/ --include="*.ts" --include="*.tsx"

# Buscar jwt.decode sem verify
grep -rn "jwt\.decode\b" src/ --include="*.ts"
```
