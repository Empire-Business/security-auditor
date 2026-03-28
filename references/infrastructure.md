# Infraestrutura e Segurança Geral

## Índice
- [OWASP Top 10 aplicado ao Supabase](#owasp)
- [Content Security Policy (CSP)](#csp)
- [Dashboard hardening](#dashboard)
- [Rate limits padrão do Supabase Auth](#rate-limits)
- [GitHub Actions para security scan contínuo](#github-actions)
- [Schema exposure — private schema e permissões](#schema)

---

## OWASP Top 10 aplicado ao Supabase {#owasp}

| Risco OWASP | Mitigação no Supabase/Next.js |
|---|---|
| **A01: Broken Access Control** | RLS em todas as tabelas + revalidar auth em cada Route Handler/Server Action |
| **A02: Cryptographic Failures** | Supabase criptografa at-rest (AES-256) e in-transit (TLS). Cookies `httpOnly` + `Secure` + `sameSite` |
| **A03: Injection** | Zod para validação de entrada + PostgREST usa queries parametrizadas. Atenção ao método `.or()` |
| **A04: Insecure Design** | RLS como defesa em profundidade + schema `private` para tabelas internas |
| **A05: Security Misconfiguration** | Security headers + Security Advisor do Dashboard + CSP |
| **A06: Vulnerable Components** | `npm audit --production` + Snyk + Dependabot |
| **A07: Identification/Auth Failures** | Supabase Auth + MFA + `getUser()` no servidor (nunca `getSession()`) |
| **A08: Software/Data Integrity** | `npm ci` em vez de `npm install` em CI + lockfile commitado |
| **A09: Logging/Monitoring** | Audit logs do Auth (`auth.audit_log_entries`) + alertas para 401/403 em massa |
| **A10: SSRF** | Validar URLs com `new URL()` server-side + verificar extensões pg_net/http no banco |

---

## Content Security Policy (CSP) {#csp}

O CSP header é a defesa mais eficaz contra XSS além da sanitização. Adicione ao `next.config.ts`:

```typescript
// next.config.ts
import type { NextConfig } from 'next'

const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline'", // Remover 'unsafe-inline' se possível
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: https:",
      "font-src 'self'",
      "connect-src 'self' https://*.supabase.co wss://*.supabase.co",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "upgrade-insecure-requests",
    ].join('; '),
  },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=()',
  },
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=63072000; includeSubDomains; preload',
  },
]

const nextConfig: NextConfig = {
  async headers() {
    return [{ source: '/(.*)', headers: securityHeaders }]
  },
}
export default nextConfig
```

**Para verificar headers existentes no projeto:**
```bash
# Checar next.config.ts por headers de segurança
grep -n "headers\|CSP\|X-Frame\|Content-Security" next.config.ts next.config.js 2>/dev/null
# Checar vercel.json
grep -n "headers\|X-Frame\|Content-Security" vercel.json 2>/dev/null
```

**Se usar vercel.json em vez de next.config.ts** (comum em projetos não-Next.js):

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
        { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()" },
        { "key": "Strict-Transport-Security", "value": "max-age=63072000; includeSubDomains; preload" }
      ]
    }
  ]
}
```

---

## Dashboard hardening {#dashboard}

Ações manuais obrigatórias no Supabase Dashboard (não automatizáveis via código):

**Conta:**
- [ ] Habilitar MFA/2FA na conta Supabase (U2F ou TOTP)
- [ ] Se usa GitHub login, habilitar 2FA no GitHub também
- [ ] Usar RBAC no org — acesso Read-Only para membros que não precisam de admin

**Banco de dados:**
- [ ] Habilitar SSL Enforcement: Database → Settings → SSL Enforcement
- [ ] Habilitar Network Restrictions (whitelist de IPs): Database → Settings → Network Restrictions
- [ ] Rodar Security Advisor: Database → Security Advisor — resolver todos os alertas

**Auth:**
- [ ] Adicionar CAPTCHA (hCaptcha ou Turnstile): Auth → Settings → CAPTCHA protection
- [ ] Configurar SMTP customizado: Auth → Settings → Email → SMTP Provider (padrão: 2 emails/hora, absurdamente baixo)
- [ ] Revisar Rate Limits: Auth → Rate Limits
- [ ] Desabilitar "Confirm email" se não estiver usando (reduz ataque de enumeração)

**Realtime:**
- [ ] Desabilitar "Allow public access": Realtime → Settings → toggle off

**API:**
- [ ] Verificar Exposed Schemas: API → Settings → confirmar que apenas schemas necessários estão expostos

---

## Rate limits padrão do Supabase Auth {#rate-limits}

| Endpoint | Limite Padrão | Risco se ultrapassado |
|---|---|---|
| Envio de emails (SMTP padrão) | 2/hora | Usuários não recebem confirmação/reset |
| Endpoints OTP | 360/hora | Brute force de OTP possível |
| Cooldown de magic link | 60s entre requisições | Spam de magic links |
| Refresh de token | 1800/hora por IP | DoS de sessões |
| MFA challenge/verify | 15/minuto por IP | Brute force de TOTP |
| Sign-in anônimo | 30/hora por IP | Criação em massa de contas anônimas |

**Verificar configuração atual:** Auth → Rate Limits no Dashboard.

**Impacto prático do SMTP padrão:** Com apenas 2 emails/hora, um app com múltiplos usuários terá confirmações e resets de senha falhando silenciosamente. Configure SMTP customizado antes de ir a produção.

---

## GitHub Actions para security scan contínuo {#github-actions}

Adicione ao projeto para scan automático a cada push e diariamente:

```yaml
# .github/workflows/security.yml
name: Security Scan
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * *' # Diariamente à meia-noite UTC

jobs:
  npm-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm audit --audit-level=high --production
        # --production ignora devDependencies (reduz falsos positivos)
```

**Verificar se o arquivo já existe:**
```bash
ls .github/workflows/ 2>/dev/null || echo "Sem GitHub Actions configurado"
cat .github/workflows/security.yml 2>/dev/null || echo "Sem security workflow"
```

**Se não existir, criar o arquivo e orientar o usuário** a commitar. O arquivo de workflow não requer secrets para `npm audit`.

---

## Schema exposure — private schema e permissões {#schema}

### O problema

O schema `public` é exposto via PostgREST (a API REST do Supabase) por padrão. Isso significa que qualquer tabela no schema `public` pode ser acessada via API REST com a anon key — RLS é a única proteção.

### Verificar schemas expostos

No Dashboard: API → Settings → **Exposed schemas**.

Via SQL:
```sql
-- Listar schemas expostos (configuração PostgREST)
SELECT setting
FROM pg_settings
WHERE name = 'pgrst.db_schemas';
```

### Criar schema privado para tabelas internas

Tabelas no schema `private` **não são acessíveis via API REST**:

```sql
-- Criar schema privado (tabelas aqui ficam fora da API)
CREATE SCHEMA IF NOT EXISTS private;

-- Mover tabela sensível para schema privado (ex: tabela de auditoria interna)
ALTER TABLE public.audit_log SET SCHEMA private;

-- Conceder acesso ao postgres apenas (não ao anon/authenticated)
GRANT USAGE ON SCHEMA private TO postgres;
```

### Revogar permissões desnecessárias de funções

Todas as funções no schema `public` são executáveis por `anon` e `authenticated` por padrão. Revogue o que não precisa ser público:

```sql
-- Ver funções executáveis por anon e authenticated
SELECT routine_name, grantee, privilege_type
FROM information_schema.routine_privileges
WHERE routine_schema = 'public'
  AND grantee IN ('anon', 'authenticated')
ORDER BY routine_name;

-- Revogar execução padrão em novas funções (aplica a partir de agora)
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  REVOKE EXECUTE ON FUNCTIONS FROM anon, authenticated;

-- Revogar de funções existentes específicas
REVOKE EXECUTE ON FUNCTION public.funcao_sensivel FROM anon, authenticated;

-- Restringir UPDATE a colunas específicas
REVOKE UPDATE ON TABLE public.users FROM authenticated;
GRANT UPDATE (display_name, avatar_url) ON TABLE public.users TO authenticated;
-- Agora authenticated pode atualizar apenas essas duas colunas
```

### Supabase Roles — referência rápida

| Role | Finalidade | Respeita RLS? |
|------|-----------|--------------|
| `anon` | Acesso público não autenticado (sem JWT) | Sim |
| `authenticated` | Usuários com JWT válido | Sim |
| `service_role` | Acesso admin server-side | **Não — bypassa todo RLS** |
| `postgres` | Superusuário do banco | **Não** |
