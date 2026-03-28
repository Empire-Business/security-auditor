# Detalhes de Auditoria por Categoria

Referência completa com SQL queries, padrões de código e exemplos de correção para cada categoria do security-auditor.

## Índice
- [Seções P0 — Crítico](#p0)
- [Seções P1 — Alto](#p1)
- [Seções P2 — Médio](#p2)
- [Ferramentas complementares](#ferramentas)

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
