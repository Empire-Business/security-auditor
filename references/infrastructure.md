# Infraestrutura e Segurança Geral

## Índice
- [OWASP Top 10:2025 aplicado ao Supabase](#owasp)
- [Content Security Policy (CSP)](#csp)
- [Dashboard hardening](#dashboard)
- [Rate limits padrão do Supabase Auth](#rate-limits)
- [GitHub Actions para security scan contínuo](#github-actions)
- [Schema exposure — private schema e permissões](#schema)
- [LGPD/GDPR — checklist de conformidade](#lgpd)
- [Supply chain security](#supply-chain)

---

## OWASP Top 10:2025 aplicado ao Supabase {#owasp}

| Risco OWASP | Mitigação no Supabase/Next.js |
|---|---|
| **A01:2025 — Broken Access Control** | RLS em todas as tabelas + revalidar auth em cada Route Handler/Server Action + negar por padrão |
| **A02:2025 — Security Misconfiguration** | Security headers + Security Advisor do Dashboard + CSP + configurações seguras por padrão |
| **A03:2025 — Software Supply Chain Failures** | `npm ci` + lockfile commitado + Dependabot/Snyk + verificação de integridade de pacotes |
| **A04:2025 — Cryptographic Failures** | Supabase criptografa at-rest (AES-256) e in-transit (TLS). Argon2id/bcrypt para senhas. Cookies `httpOnly` + `Secure` + `sameSite` |
| **A05:2025 — Injection** | Zod para validação de entrada + PostgREST usa queries parametrizadas. Atenção ao método `.or()` |
| **A06:2025 — Insecure Design** | RLS como defesa em profundidade + schema `private` + threat modeling + privacidade por design |
| **A07:2025 — Authentication Failures** | Supabase Auth + MFA + `getUser()` no servidor + brute force protection + account lockout |
| **A08:2025 — Software/Data Integrity Failures** | SRI hashes + assinatura de commits + verificação de dependências |
| **A09:2025 — Security Logging & Alerting Failures** | Audit logs do Auth (`auth.audit_log_entries`) + alertas para 401/403 em massa + SIEM |
| **A10:2025 — Mishandling of Exceptional Conditions** | Fail-safe defaults + error handling que não expõe detalhes + tratamento de estados anormais |

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
      // CSP forte = sem 'unsafe-inline'. Use nonce por request (middleware) + 'strict-dynamic'.
      "script-src 'self' 'nonce-${nonce}' 'strict-dynamic'",
      "style-src 'self' 'nonce-${nonce}'",
      "img-src 'self' data: https://*.supabase.co", // allowlist explícita — NUNCA https: genérico
      "font-src 'self'",
      "connect-src 'self' https://*.supabase.co wss://*.supabase.co",
      "object-src 'none'",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "upgrade-insecure-requests",
      // "require-trusted-types-for 'script'", // ativar quando o app estiver pronto
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
- [ ] Manter "Confirm email" ATIVADO — desligar permite account pre-creation/squatting com e-mail de terceiro. Mitigue enumeração com resposta genérica + rate limit (tasks 1c/3d), não desativando verificação

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

**Hardening obrigatório (v1.9):**
- `permissions: contents: read` no topo do workflow (negar write por padrão ao `GITHUB_TOKEN`).
- **Nunca** use `pull_request_target` com acesso a secrets em código de fork (exfiltra `SUPABASE_SERVICE_ROLE_KEY`/`ACCESS_TOKEN`). Prefira `pull_request` + environments protegidos.
- Deploy sem secret estático via **OIDC** (`id-token: write`) para Supabase/Vercel.
- **Pine ações por SHA** (`uses: actions/checkout@<sha>`), não por tag móvel.
- Habilite **branch protection** + **environment protection rules** e revise artefatos entre jobs.

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

---

## LGPD/GDPR — checklist de conformidade {#lgpd}

### Bases legais de tratamento (art. 7º, LGPD)

Antes de coletar qualquer dado pessoal, identifique a base legal:
- Consentimento do titular
- Cumprimento de obrigação legal/regulatória
- Execução de contrato
- Exercício regular de direitos em processo judicial
- Proteção da vida
- Tutela da saúde
- Interesse legítimo do controlador ou terceiro
- Proteção do crédito

### Checklist técnico

- [ ] **Inventário de dados pessoais**: mapear tabelas e colunas com PII
- [ ] **Consentimento**: granular, claro, registrado e revogável
- [ ] **Direitos do titular**: acesso, correção, eliminação, portabilidade, anonimização, oposição
- [ ] **Retenção**: política de tempo de retenção e eliminação automática
- [ ] **Segurança**: criptografia, RLS, MFA, logs de acesso
- [ ] **Cookies/rastreamento**: banner de consentimento antes de qualquer tracker
- [ ] **Third-parties**: DPA assinado com fornecedores que processam dados
- [ ] **Transferência internacional**: SCCs ou país com adequação da ANPD
- [ ] **DPO**: nomeado se processamento em larga escala ou dados sensíveis
- [ ] **DPIA/RIPD**: avaliação de impacto para tratamentos de alto risco
- [ ] **Incidentes**: rotina de resposta e notificação à ANPD em até **3 dias úteis** (6 para agente de pequeno porte) a partir do conhecimento — Res. CD/ANPD 15/2024. ⚠️ Não confundir com os "72h" do GDPR.
- [ ] **Política de privacidade**: clara, acessível e atualizada

### Cookies e trackers

Não carregue scripts de analytics/ads antes do consentimento. Exemplo de carregamento condicional:

```typescript
function Analytics() {
  const consent = useCookieConsent()
  if (!consent.analytics) return null
  return <script src="https://analytics.example.com/script.js" async />
}
```

### Notificação de incidente à ANPD

Em caso de vazamento, prepare:
1. Relatório técnico do incidente
2. Dados e titulares potencialmente afetados
3. Medidas de contenção e mitigação adotadas
4. Comunicação aos titulares quando aplicável

---

## Supply chain security {#supply-chain}

### Checklist de segurança da cadeia de suprimentos

- [ ] Lockfile sempre commitado
- [ ] CI usa `npm ci` / equivalente com frozen lockfile
- [ ] Dependências pinadas para pacotes críticos
- [ ] `.npmrc` com `engine-strict=true` e `package-lock=true`
- [ ] Revisão de `postinstall`/`preinstall` scripts
- [ ] Dependabot ou Renovate habilitado
- [ ] `npm audit` no CI com `--audit-level=high`
- [ ] Assinatura de commits (Git commit signing)
- [ ] Verificação de integridade de artefatos de build

### GitHub Actions seguro

```yaml
name: Security Scan
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm audit --audit-level=high --production
      - name: Check for secrets
        run: |
          npx secretlint "**/*" || true
```
