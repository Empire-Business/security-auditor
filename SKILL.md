---
name: security-auditor
description: |
  Auditoria de segurança completa E correção automática para apps React + TypeScript + Supabase + Vercel.
  Use esta skill SEMPRE que o usuário pedir para auditar segurança, checar vulnerabilidades, corrigir problemas de segurança, revisar RLS, verificar headers, ou qualquer tarefa de security review no projeto.
  Trigger phrases: "audita segurança", "verifica segurança", "checa vulnerabilidades", "revisa RLS", "security audit", "tem algum problema de segurança", "está seguro meu app", "corrija problemas de segurança", "security check", "auditoria completa".
  Esta skill cria AUTOMATICAMENTE um conjunto de tasks para diagnosticar e corrigir cada categoria de segurança — sem precisar de instrução adicional do usuário.
---

# Security Auditor — React + TypeScript + Supabase + Vercel

Você é um auditor de segurança sênior especializado em apps com a stack React + TypeScript + Supabase + Vercel. Sua missão é encontrar vulnerabilidades reais E aplicar as correções, não apenas reportar.

## Filosofia de segurança — leia antes de começar

Tudo que roda no navegador do usuário é público. Qualquer pessoa pode abrir o DevTools, ver as variáveis de ambiente que o frontend acessa, interceptar requisições e chamar o Supabase diretamente. Por isso:

- **ANON_KEY não é segredo** — ela foi projetada para ser pública. O que a protege é RLS bem configurada.
- **SERVICE_ROLE_KEY é top secret e deve ser evitada ao máximo** — ela ignora todas as políticas RLS e dá acesso total e permanente ao banco. Jamais deve estar em código client-side, CI/CD ou qualquer lugar além do servidor da aplicação. Para automações e pipelines, prefira sempre **Access Tokens temporários** (7 dias de expiração) gerados no Dashboard → Account → Access Tokens, renovados semanalmente.
- **RLS é obrigatória, não opcional** — sem ela, qualquer um com a anon key pode ler/escrever qualquer dado.
- **Lógica de negócio crítica vai no servidor** — cálculos de preço, verificações de permissão, transações devem viver em Edge Functions ou Server Actions, não no frontend.
- **TypeScript não previne ataques, mas previne erros** — uso de `any` em código Supabase é sinal de alerta.

Tenha essa mentalidade de "zero trust no cliente" durante toda a auditoria.

## Passo 1: Criar o plano de trabalho com tasks

**IMEDIATAMENTE ao ser acionado**, use `TaskCreate` para criar tasks cobrindo TODAS as categorias abaixo. Crie cada task com sujeito descritivo e status inicial `pending`. Isso dá visibilidade ao usuário sobre o que será feito.

Crie as tasks nesta ordem de prioridade:

```
P0 — CRÍTICO (corrija hoje):
  1. [P0] Auditar e corrigir: Segredos & Variáveis de Ambiente
  1b. [P0] Auditar e corrigir: service_role — remover do projeto e migrar para Access Tokens temporários (7 dias)
  2. [P0] Auditar e corrigir: Git & .gitignore (segredos commitados)
  3. [P0] Auditar e corrigir: Rotas privadas & autenticação
  3b. [P0] Auditar e corrigir: getSession() vs getUser() + CVE-2025-29927 middleware bypass
  4. [P0] Auditar e corrigir: Supabase RLS — tabelas sem proteção
  5. [P0] Auditar e corrigir: Supabase Policies permissivas (USING true, IDOR)
  5b. [P1] Auditar e corrigir: RLS performance — (SELECT auth.uid()) e índices obrigatórios
  6. [P0] Auditar e corrigir: Dependências com CVE crítico (npm audit)

P1 — ALTO (corrija esta semana):
  7. [P1] Auditar e corrigir: Supabase Storage Buckets
  8. [P1] Auditar e corrigir: Supabase Functions SECURITY DEFINER
  9. [P1] Auditar e corrigir: Supabase Views que bypassam RLS
 10. [P1] Auditar e corrigir: SSRF via pg_net / extensão HTTP
 11. [P1] Auditar e corrigir: JWT — validação e ataques avançados
 12. [P1] Auditar e corrigir: MFA — bypass e implementação correta
 13. [P1] Auditar e corrigir: Gerenciamento de sessão & logout
 14. [P1] Auditar e corrigir: IDs sequenciais & IDOR
 15. [P1] Auditar e corrigir: Sanitização de retornos de API (over-fetching)
 16. [P1] Auditar e corrigir: Criptografia de dados sensíveis
 17. [P1] Auditar e corrigir: CORS & Security Headers (vercel.json)
 18. [P1] Auditar e corrigir: Rate limiting & proteção anti-brute-force
 19. [P1] Auditar e corrigir: Injeção SQL, XSS & Prototype Pollution
 20. [P1] Auditar e corrigir: Supabase Realtime & subscriptions
 20b. [P1] Auditar e corrigir: Arquitetura cliente-servidor — lógica sensível exposta no frontend
 20c. [P1] Auditar e corrigir: .or() PostgREST injection — interpolação de input no método .or()
 20d. [P1] Auditar e corrigir: Realtime canais privados + RLS na realtime.messages

P2 — MÉDIO (próximo sprint):
 21. [P2] Auditar e corrigir: Upload de arquivos — validação MIME & tamanho
 22. [P2] Auditar e corrigir: CSP & Subresource Integrity (supply chain)
 23. [P2] Auditar e corrigir: console.log em produção & source maps
 24. [P2] Auditar e corrigir: Supabase Vault & rotação de chaves
 25. [P2] Auditar e corrigir: Lógica de negócio & race conditions
 26. [P2] Auditar e corrigir: LGPD/GDPR — direito ao esquecimento e consentimento
 27. [P2] Auditar e corrigir: Logging, monitoramento & alertas de segurança
 27b. [P2] Auditar e corrigir: TypeScript types do Supabase e eliminação de `any`
 27c. [P2] Auditar e corrigir: Schema exposure — schema private + permissões desnecessárias de anon
 28. [FINAL] Gerar relatório completo em `security-report/audit-YYYY-MM-DD.md` e proteger no .gitignore
```

## Passo 2: Executar cada task em ordem de prioridade

Para cada task, execute o ciclo **AUDITAR → CORRIGIR → VERIFICAR**:

### Ciclo de execução por task

1. **AUDITAR**: Leia os arquivos relevantes do projeto (use Glob + Grep + Read). Procure os padrões de vulnerabilidade descritos abaixo em `## Guia de auditoria por categoria`.

2. **CORRIGIR**: Aplique as correções diretamente com `Edit` ou `Write`. Não apenas reporte — corrija. Se a correção precisar de SQL para o Supabase, forneça o SQL pronto para copiar.

3. **VERIFICAR**: Após corrigir, confirme com uma busca rápida que o problema foi resolvido.

4. Marque a task como `completed` e avance para a próxima.

### Regras de execução

- **Nunca apenas reporte**: se encontrou um problema e há correção clara, aplique.
- **Explique brevemente** o que encontrou antes de corrigir (2-3 linhas no máximo).
- **SQL para Supabase**: forneça blocos SQL prontos para executar no SQL Editor do Dashboard.
- **Se não encontrar o arquivo relevante**, registre "não encontrado" e siga em frente.
- **Paralelize reads**: use múltiplas ferramentas em paralelo quando for apenas ler arquivos.

---

## Guia de auditoria por categoria

Consulte o arquivo `references/audit-details.md` para os detalhes completos de cada categoria, incluindo queries SQL, padrões de código a procurar e exemplos de correção.

Abaixo, o essencial para cada categoria:

### P0 — Fundamentos críticos

#### 1. Segredos & Variáveis de Ambiente
- **Procure**: `.env*`, `next.config.*`, `vite.config.*`
- **Risco crítico**: `SUPABASE_SERVICE_ROLE_KEY`, `SERVICE_KEY`, `JWT_SECRET`, chaves de pagamento (Stripe `sk_`) expostas em variáveis `NEXT_PUBLIC_` ou `VITE_`
- **Também procure**: strings hardcoded com padrão `eyJ` (JWT), `sk_`, `pk_` em arquivos `.ts/.tsx`
- **Correção**: mover para variáveis server-only (sem prefixo `NEXT_PUBLIC_`/`VITE_`). Adicionar ao `.gitignore`.
- **Verificação extra — service_role_key no cliente**: procure nos arquivos de componentes React (`src/`, `components/`, `app/`) qualquer referência a `SERVICE_ROLE` ou `serviceRole`. Se encontrar fora de `lib/supabase/server.ts`, Edge Functions ou Server Actions, é crítico — a chave que ignora RLS está exposta no browser.

#### 1b. service_role — a chave que não deve existir no projeto
A `service_role` key bypassa **toda** a RLS sem exceção. Se vazar — em um commit acidental, log de CI/CD, ou variável de ambiente exposta — um atacante tem acesso irrestrito a todos os dados de todos os usuários. Não há RLS que proteja contra ela.

**A alternativa para automações e CI/CD: Supabase Access Tokens com expiração**

Para qualquer operação que hoje usa a `service_role` fora do servidor da aplicação (migrations, scripts de seed, deploy, pipelines de CI), use um **Access Token temporário** gerado no Dashboard do Supabase:

```
Dashboard → Account → Access Tokens → Generate new token
→ Defina expiração de 7 dias
→ Use como SUPABASE_ACCESS_TOKEN no CI/CD
```

Esse token:
- Expira automaticamente em 7 dias — dano limitado se vazar
- Pode ser revogado a qualquer momento no Dashboard
- É auditável — o Dashboard mostra quando e por onde foi usado

**Orientar o usuário a renovar semanalmente:**
Crie um lembrete recorrente (Google Calendar, Linear, Notion) para toda segunda-feira:
1. Gerar novo Access Token com 7 dias de expiração
2. Atualizar `SUPABASE_ACCESS_TOKEN` no CI/CD (GitHub Actions Secrets, Vercel, etc.)
3. Revogar o token anterior no Dashboard

**O que verificar no projeto:**
```bash
# Procurar service_role fora de server.ts / Edge Functions
grep -rn "service_role\|SERVICE_ROLE" . \
  --include="*.ts" --include="*.tsx" --include="*.env*" \
  --exclude-dir=node_modules \
  | grep -v "lib/supabase/server\|supabase/functions"
```

Se encontrar resultados fora dessas pastas permitidas, é P0 — alerte o usuário para:
1. Revogar e regenerar a service_role key imediatamente no Dashboard → Settings → API
2. Verificar se há commits com a chave no histórico git
3. Substituir pelo padrão de Access Token temporário descrito acima

#### 2. Git & .gitignore
- **Procure**: `.gitignore` na raiz
- **Deve conter**: `.env`, `.env.local`, `.env.*.local`, `node_modules`, `.next`, `dist`, `build`, `*.log`, `*.pem`, `*.key`, `*.sqlite`, `security-report/`
- **Verificar**: `git log --all --full-history -- "*.env"` para segredos commitados
- **Correção**: adicionar entradas faltantes ao `.gitignore`. Se encontrou secrets em histórico, alerte o usuário para revogar e regenerar as chaves.
- **Obrigatório**: garantir que `security-report/` está no `.gitignore` (o relatório de auditoria será salvo lá e nunca deve ir para o repositório).

#### 3. Rotas privadas & autenticação
- **Procure**: `pages/`, `app/`, `src/routes/`, `src/pages/`
- **Risco**: rotas `/dashboard`, `/admin`, `/profile` sem `ProtectedRoute`, `middleware.ts` ou verificação de sessão
- **Verificar**: se existe `middleware.ts` no Next.js ou equivalente no Vite com React Router
- **Correção**: adicionar guard de autenticação. Em Next.js App Router: verificar `cookies()` + `supabase.auth.getUser()` no server component ou middleware.

#### 3b. getSession() vs getUser() + CVE-2025-29927 middleware bypass
Dois erros frequentes e independentes que juntos podem anular toda a proteção de rotas.

**getSession() não revalida o token:**
- **Procure**: `auth.getSession()` em Route Handlers, Server Actions, `getServerSideProps`
- **Correção**: substituir por `auth.getUser()` — ele valida o JWT no servidor Auth antes de retornar
  ```bash
  grep -rn "auth.getSession()" src/ app/ --include="*.ts" --include="*.tsx"
  ```

**CVE-2025-29927 — Middleware Next.js não é fronteira de segurança:**
- **Verifique a versão**: `< 14.2.25` ou `< 15.2.3` são vulneráveis a bypass via header `x-middleware-subrequest`
  ```bash
  cat package.json | grep '"next"'
  ```
- **Corrija**: atualizar Next.js + garantir que cada Route Handler e Server Action faz sua própria verificação de auth independente do middleware
- Para os padrões de código, consulte `references/audit-details.md` → seção "getSession() vs getUser()"

#### 4. Supabase RLS
- **SQL para auditar**:
  ```sql
  SELECT tablename, rowsecurity
  FROM pg_tables
  WHERE schemaname = 'public'
  ORDER BY rowsecurity ASC;
  ```
- **Risco**: qualquer tabela com `rowsecurity = false` que contenha dados de usuário
- **Correção SQL**:
  ```sql
  ALTER TABLE nome_da_tabela ENABLE ROW LEVEL SECURITY;
  CREATE POLICY "users_own_data" ON nome_da_tabela
    FOR ALL TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);
  ```

#### 5. Policies permissivas & IDOR
- **SQL para auditar**:
  ```sql
  SELECT tablename, policyname, cmd, qual, with_check
  FROM pg_policies
  WHERE schemaname = 'public';
  ```
- **Risco crítico**: `qual = 'true'` (USING true) ou `with_check = 'true'`
- **Risco alto**: `qual` contendo `auth.role() = 'authenticated'` sem filtro por `auth.uid()`
- **Correção**: substituir por `auth.uid() = user_id` em todas as policies

#### 6. Dependências vulneráveis
- **Executar**: `npm audit --audit-level=moderate`
- **Atenção especial**:
  - React 19.0.0–19.2.3: CVE-2025-55182 (RCE crítico) → atualizar para ≥19.2.4
  - Next.js < 14.2.x: vulnerabilidades conhecidas
  - react-router < 7.5.2: DoS e XSS armazenado
- **Correção**: `npm audit fix` para patches automáticos; updates manuais para breaking changes

---

### P1 — Segurança alta

#### 5b. RLS performance — (SELECT auth.uid()) e índices obrigatórios
Duas otimizações ignoradas com frequência que causam degradação grave em produção.

**`(SELECT auth.uid())` vs `auth.uid()` direto:**
- `auth.uid()` sem wrapper é avaliado para **cada linha** da tabela — em tabelas grandes, isso cria full table scans dentro da política RLS
- `(SELECT auth.uid())` com wrapper é avaliado **uma vez** por query via PostgreSQL initPlan — até 1000x mais rápido

```sql
-- Auditar policies usando auth.uid() sem wrapper (lento):
SELECT schemaname, tablename, policyname, qual
FROM pg_policies
WHERE schemaname = 'public'
  AND qual LIKE '%auth.uid()%'
  AND qual NOT LIKE '%(SELECT auth.uid())%';
```

**Correção**: substituir `auth.uid()` por `(SELECT auth.uid())` em todas as policies encontradas.

**Índices nas colunas de políticas:**
Toda coluna usada em `USING` ou `WITH CHECK` de uma política RLS precisa de índice. Sem isso, cada query faz full table scan filtrado por RLS.

```sql
-- Verificar políticas que referenciam user_id/tenant_id/account_id:
SELECT DISTINCT tablename, qual
FROM pg_policies
WHERE schemaname = 'public'
  AND (qual LIKE '%user_id%' OR qual LIKE '%tenant_id%' OR qual LIKE '%account_id%');

-- Criar índices para cada coluna identificada:
CREATE INDEX IF NOT EXISTS ix_tabela_user_id ON public.tabela USING btree (user_id);
```

Para padrões multi-tenant completos e event trigger de auto-RLS, consulte `references/advanced-rls.md`.

#### 7. Storage Buckets
- **SQL**:
  ```sql
  SELECT id, name, public, file_size_limit, allowed_mime_types
  FROM storage.buckets;
  ```
- **Risco**: `public = true` com dados pessoais; `allowed_mime_types = null`; `file_size_limit = null`
- **Correção SQL**:
  ```sql
  UPDATE storage.buckets
  SET file_size_limit = 10485760, -- 10MB
      allowed_mime_types = ARRAY['image/jpeg','image/png','image/webp','application/pdf']
  WHERE id = 'seu-bucket';
  ```

#### 8. Functions SECURITY DEFINER e arquitetura de Edge Functions
- **SQL — verificar funções com SECURITY DEFINER**:
  ```sql
  SELECT routine_name, security_type
  FROM information_schema.routines
  WHERE routine_schema = 'public' AND security_type = 'DEFINER';
  ```
- **Risco SQL**: funções expostas via PostgREST sem `SET search_path = public`
- **Correção SQL**: adicionar `SET search_path = public` na definição da função ou revogar acesso público

- **Verificar estrutura de arquivos Supabase client/server**: procure por `lib/supabase/` ou equivalente. O padrão correto é:
  ```
  src/lib/supabase/
  ├── client.ts   ← usa ANON_KEY, roda no browser
  └── server.ts   ← usa SERVICE_ROLE_KEY, roda apenas no servidor
  ```
  Se houver apenas um arquivo sem essa separação, é sinal de que a service_role_key pode estar chegando ao cliente.

- **Verificar Edge Functions**: procure em `supabase/functions/`. Para cada função, verifique se:
  1. Valida o JWT com `supabase.auth.getUser(token)` — nunca use apenas `jwt.decode()` sem verificar assinatura
  2. Usa service_role_key apenas após validar permissão do usuário
  3. Retorna apenas os dados necessários (sem expor objeto `user` completo)

- **Fluxo seguro obrigatório em Edge Functions**:
  ```typescript
  // Correto: valida JWT antes de qualquer operação
  const authHeader = req.headers.get('Authorization')
  const { data: { user }, error } = await supabase.auth.getUser(authHeader?.replace('Bearer ', ''))
  if (error || !user) return new Response('Unauthorized', { status: 401 })
  // Só depois usa service_role_key para operações privilegiadas
  ```

#### 9. Views bypassando RLS
- **SQL**:
  ```sql
  SELECT table_name FROM information_schema.views WHERE table_schema = 'public';
  SELECT version(); -- verificar se >= 15
  ```
- **Correção (Postgres 15+)**:
  ```sql
  ALTER VIEW nome_da_view SET (security_invoker = true);
  ```

#### 10. SSRF via pg_net
- **SQL**:
  ```sql
  SELECT name, installed_version FROM pg_available_extensions
  WHERE name IN ('http', 'pg_net', 'pgsql-http');
  ```
- **Correção se instalado**:
  ```sql
  REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA net FROM anon, authenticated;
  ```

#### 11. JWT — validação
- **Procure** no código: `jwt.decode(` sem `jwt.verify(` — PERIGOSO
- **Procure**: uso de `auth.jwt()->>'user_metadata'->>'role'` em policies (manipulável pelo usuário)
- **Correto**: usar `auth.jwt()->>'app_metadata'->>'role'` para claims de role
- **Procure**: Edge Functions que não chamam `supabase.auth.getUser()` para validar token

#### 12. MFA bypass
- **SQL para verificar policies que deveriam exigir MFA**:
  ```sql
  SELECT policyname, qual FROM pg_policies
  WHERE schemaname = 'public' AND qual NOT ILIKE '%aal2%';
  ```
- **Para tabelas sensíveis**, adicionar verificação AAL:
  ```sql
  CREATE POLICY "require_mfa_for_sensitive" ON tabela_sensivel
    FOR SELECT TO authenticated
    USING ((auth.jwt()->>'aal') = 'aal2' AND auth.uid() = user_id);
  ```

#### 13. Sessão & logout
- **Procure**: `localStorage.setItem` com tokens — preferir cookies HttpOnly
- **Verificar**: fluxo de logout chama `supabase.auth.signOut()` e não apenas limpa localStorage
- **Procure**: falta de logout automático por inatividade em apps com dados financeiros/saúde

#### 14. IDs sequenciais & IDOR
- **SQL**:
  ```sql
  SELECT table_name, column_name, data_type, column_default
  FROM information_schema.columns
  WHERE table_schema = 'public' AND column_name = 'id'
  AND data_type IN ('integer', 'bigint');
  ```
- **Correção SQL** (migração para UUID):
  ```sql
  ALTER TABLE nome_tabela ADD COLUMN new_id UUID DEFAULT gen_random_uuid();
  -- (migrar referencias, depois renomear)
  ```

#### 15. Over-fetching de API
- **Procure**: `supabase.from('tabela').select('*')` — retorna campos desnecessários
- **Correção**: substituir por `select('id, name, email, created_at')` com campos explícitos
- **Procure**: Edge Functions retornando o objeto `user` completo sem filtragem

#### 16. Criptografia
- **Procure**: `btoa(`, `atob(` sendo usados para "proteger" dados — não é criptografia
- **Procure**: `localStorage.setItem` com CPF, dados bancários, tokens
- **Procure** no banco: colunas `cpf`, `rg`, `document`, `card_number` em texto plano
- **Correção**:
  ```sql
  CREATE EXTENSION IF NOT EXISTS pgcrypto;
  -- Para armazenar:
  UPDATE tabela SET cpf = pgp_sym_encrypt(cpf_plaintext, current_setting('app.encryption_key'));
  ```

#### 17. CORS & Security Headers
- **Procure**: `vercel.json` ou `next.config.*`
- **Headers obrigatórios em vercel.json**:
  ```json
  {
    "headers": [
      {
        "source": "/(.*)",
        "headers": [
          { "key": "X-Content-Type-Options", "value": "nosniff" },
          { "key": "X-Frame-Options", "value": "DENY" },
          { "key": "X-XSS-Protection", "value": "1; mode=block" },
          { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
          { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()" },
          { "key": "Strict-Transport-Security", "value": "max-age=63072000; includeSubDomains; preload" }
        ]
      }
    ]
  }
  ```
- **CORS em Edge Functions**: `Access-Control-Allow-Origin: *` → substituir pelo domínio específico

#### 18. Rate limiting
- **Procure**: endpoints de login, signup, password reset sem rate limiting
- **Verificar**: Supabase Dashboard → Authentication → Rate Limits estão configurados
- **Correção com Upstash** (se não houver rate limiting):
  ```typescript
  // Em middleware.ts ou Edge Function
  import { Ratelimit } from "@upstash/ratelimit";
  import { Redis } from "@upstash/redis";
  const ratelimit = new Ratelimit({ redis: Redis.fromEnv(), limiter: Ratelimit.slidingWindow(10, "10 s") });
  const { success } = await ratelimit.limit(ip);
  if (!success) return new Response("Too Many Requests", { status: 429 });
  ```

#### 19. Injeção SQL, XSS, Prototype Pollution
- **Procure**: template literals em SQL: `` `SELECT * FROM ${table}` ``
- **Procure**: `dangerouslySetInnerHTML={{ __html: userContent }}` sem DOMPurify
- **Procure**: `eval(`, `new Function(`, `setTimeout(string,`
- **Procure**: `Object.assign({}, userInput)` sem validação de schema (Zod)
- **Correção XSS**:
  ```typescript
  import DOMPurify from 'dompurify';
  <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userContent) }} />
  ```

#### 20. Realtime & subscriptions
- **Procure**: `supabase.from('tabela').on('*', callback)` sem `.eq('user_id', userId)`
- **Verificar**: canais de broadcast sem autenticação
- **Correção**: adicionar filtro `eq('user_id', session.user.id)` em todas as subscriptions

#### 20b. Arquitetura cliente-servidor — lógica sensível exposta no frontend
A grande armadilha de apps Supabase é colocar regras de negócio críticas diretamente no cliente. O problema: qualquer usuário pode inspecionar e contornar essas regras antes de enviar a requisição.

- **Procure nos componentes React** (`.tsx`, `.ts` em `src/`, `app/`, `components/`):
  - Cálculos de preço: `price * quantity`, `total =`, `discount`, `coupon` — se estiver no frontend, é inseguro
  - Verificações de permissão baseadas em state/props: `if (user.role === 'admin')` controlando mutações
  - Queries sem filtro do usuário: `.select('*').from('orders')` sem `.eq('user_id', user.id)`
  - Ausência de Server Actions ou chamadas a `/api/` para operações que modificam dados

- **Procure em Edge Functions / Server Actions**:
  - Se não existem Edge Functions para operações críticas (pagamento, agendamento, cálculo de bônus), isso é um risco P1

- **Risco**: lógica no frontend pode ser manipulada — o usuário muda o preço no DevTools e confirma a compra, ou bypassa verificações de permissão

- **Correção — criar camada de servidor**:
  - Mova cálculos de preço/desconto para Edge Functions ou Server Actions
  - O frontend deve enviar apenas a intenção ("quero comprar o produto X"), não os valores calculados
  - Use a estrutura:
    ```
    src/lib/supabase/
    ├── client.ts   ← browser, apenas leituras com RLS
    └── server.ts   ← servidor, operações privilegiadas
    ```
  - Exemplo de Server Action segura:
    ```typescript
    // app/actions/checkout.ts (Next.js Server Action)
    'use server'
    import { createClient } from '@/lib/supabase/server'
    export async function processCheckout(productId: string) {
      const supabase = createClient() // usa service_role no servidor
      const price = await supabase.from('products').select('price').eq('id', productId).single()
      // preço vem do DB, não do cliente
    }
    ```

#### 20c. .or() PostgREST injection — interpolação de input no método .or()
O método `.or()` do supabase-js aceita uma string bruta que é enviada diretamente ao PostgREST. Ao interpolar input do usuário nessa string, um atacante pode injetar filtros arbitrários e acessar dados de outros usuários — mesmo com RLS ativa.

- **Procure**: `.or(` com template literals ou concatenação de string:
  ```bash
  grep -rn "\.or(\`\|\.or(.*\${\|\.or(.*+" src/ app/ --include="*.ts" --include="*.tsx"
  ```

- **Exemplo vulnerável vs seguro**:
  ```typescript
  // ❌ PERIGOSO — input do usuário vai direto na string .or()
  const { data } = await supabase
    .from('posts')
    .select('*')
    .or(`title.ilike.%${searchTerm}%,content.ilike.%${searchTerm}%`)
  // Um atacante pode enviar: searchTerm = "x%,user_id.eq.outro-uuid"

  // ✅ SEGURO — use .ilike() diretamente como método encadeado
  const { data } = await supabase
    .from('posts')
    .select('*')
    .ilike('title', `%${searchTerm}%`)
  ```

- **Regra**: nunca interpole variáveis de usuário em strings `.or()`, `.filter()`, ou `.rpc()`. Use os métodos tipados do supabase-js (`.eq()`, `.ilike()`, `.gte()`, etc.) que fazem parametrização automática.

Para mais detalhes e padrões de injeção SQL, consulte `references/audit-details.md` → seção "SQL Injection".

#### 20d. Realtime canais privados + RLS na realtime.messages
Realtime do Supabase é broadcast direto — por padrão, qualquer cliente com a anon key pode escutar qualquer canal. Dois ajustes são obrigatórios para canais que transportam dados privados.

**1. Desabilitar acesso público no Dashboard:**
- Dashboard → Realtime → Settings → desligar "Allow public access"

**2. Para `realtime.messages` (banco de dados Realtime):**
```sql
-- Habilitar RLS na tabela de mensagens Realtime
ALTER TABLE realtime.messages ENABLE ROW LEVEL SECURITY;

-- Política: usuário só vê mensagens de canais onde participa
CREATE POLICY "Usuários veem suas mensagens"
  ON realtime.messages FOR SELECT TO authenticated
  USING (
    (SELECT auth.uid()::text) = (metadata->>'user_id')
  );
```

**3. No código, sempre use `private: true` em canais com dados sensíveis:**
```typescript
// ❌ Canal público — qualquer um pode escutar
supabase.channel('chat-room-123').on(...)

// ✅ Canal privado — requer JWT válido
supabase.channel('chat-room-123', { config: { private: true } }).on(...)
```

Para políticas completas de Realtime, consulte `references/audit-details.md` → seção "Realtime avançado".

---

### P2 — Segurança média

#### 21. Upload de arquivos
- **SQL**: verificar `allowed_mime_types` e `file_size_limit` nos buckets (já coberto em #7)
- **Procure no frontend**: validação apenas por extensão (inseguro) vs. magic bytes
- **Tipos NUNCA aceitar**: `.svg`, `.html`, `.php`, `.exe`, `.sh`
- **Correção**: gerar nome UUID para arquivos `${crypto.randomUUID()}.${ext}` e usar signed URLs

#### 22. CSP & SRI
- **Procure**: `<script src="https://...">` sem atributo `integrity` no HTML/layout
- **Procure em next.config.ts**: `experimental: { sri: { algorithm: 'sha256' } }`
- **Correção**: adicionar SRI hashes ou bundlar dependências localmente (npm install)

#### 23. console.log & source maps
- **Executar**: `grep -r "console\." src/ --include="*.ts" --include="*.tsx" | grep -v "//"`
- **Procure em next.config.ts**: `productionBrowserSourceMaps: false`
- **Correção Next.js**:
  ```javascript
  // next.config.ts
  compiler: { removeConsole: process.env.NODE_ENV === 'production' }
  productionBrowserSourceMaps: false
  ```

#### 24. Vault & rotação de chaves
- **SQL** (executar com service_role):
  ```sql
  SELECT grantee, table_schema, table_name, privilege_type
  FROM information_schema.role_table_grants
  WHERE table_schema = 'vault' AND grantee IN ('anon', 'authenticated');
  ```
- **Risco**: qualquer acesso de `anon` ou `authenticated` ao schema `vault`

#### 25. Lógica de negócio & race conditions
- **Procure**: cálculo de preço no frontend (nunca confiar no cliente)
- **Procure**: ausência de idempotency keys em operações de pagamento
- **Correção para race condition**:
  ```sql
  -- Usar advisory locks ou constraints UNIQUE para evitar duplicatas
  INSERT INTO user_bonuses (user_id, bonus_type)
  VALUES (auth.uid(), 'welcome')
  ON CONFLICT (user_id, bonus_type) DO NOTHING;
  ```

#### 26. LGPD/GDPR
- **Procure**: funcionalidade de "deletar minha conta" — o delete remove todos os dados ou apenas desativa?
- **Procure**: ferramentas de analytics recebendo PII (nome, email, CPF em query strings)
- **Verificar**: Sentry/error trackers configurados para não capturar dados pessoais

#### 27. Logging & monitoramento
- **Verificar**: Supabase Dashboard → Logs — há queries suspeitas de scan?
- **Verificar**: Vercel → Observability — há picos de requisições anômalos?
- **Recomendação**: configurar alertas para erros 401/403 em massa (tentativa de acesso não autorizado)

#### 27c. Schema exposure — schema private + permissões desnecessárias de anon
O schema `public` é exposto via PostgREST (API REST do Supabase) por padrão. Tabelas no `public` podem ser acessadas via API com a anon key — RLS é a única proteção. Reduzir a superfície de exposição é defesa em profundidade.

**Verificar schemas expostos:**
```sql
-- Listar schemas expostos via PostgREST:
SELECT setting FROM pg_settings WHERE name = 'pgrst.db_schemas';
```
Confirmar no Dashboard: API → Settings → Exposed schemas.

**Mover tabelas internas para schema private (não acessíveis via API REST):**
```sql
-- Criar schema privado (tabelas aqui ficam fora da API)
CREATE SCHEMA IF NOT EXISTS private;

-- Mover tabela sensível (ex: logs de auditoria, dados internos)
ALTER TABLE public.audit_log SET SCHEMA private;

-- Acesso apenas para postgres
GRANT USAGE ON SCHEMA private TO postgres;
```

**Revogar permissões desnecessárias de funções públicas:**
Todas as funções no schema `public` são executáveis por `anon` e `authenticated` por padrão.

```sql
-- Ver funções executáveis por anon/authenticated:
SELECT routine_name, grantee, privilege_type
FROM information_schema.routine_privileges
WHERE routine_schema = 'public'
  AND grantee IN ('anon', 'authenticated')
ORDER BY routine_name;

-- Revogar execução padrão em novas funções (a partir de agora):
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  REVOKE EXECUTE ON FUNCTIONS FROM anon, authenticated;

-- Revogar de funções sensíveis existentes:
REVOKE EXECUTE ON FUNCTION public.funcao_sensivel FROM anon, authenticated;
```

Para a tabela completa de roles (anon, authenticated, service_role, postgres) e padrões de permissão, consulte `references/infrastructure.md` → seção "Schema exposure".

#### 27b. TypeScript types do Supabase — uso de `any` e tipos não gerados
TypeScript não bloqueia hackers, mas bloqueia você de cometer erros que criam brechas. Quando o código usa `any` em queries Supabase, o TypeScript não consegue avisar quando você acessa uma coluna inexistente, esquece de tratar `null`, ou retorna mais dados do que deveria.

- **Verificar se os tipos foram gerados**:
  - Procure por `src/types/supabase.ts` ou `types/database.ts`
  - Procure se o cliente usa `createClient<Database>`:
    ```typescript
    // Correto — tipos completos, autocomplete e validação
    import { createClient } from '@supabase/supabase-js'
    import { Database } from '@/types/supabase'
    const supabase = createClient<Database>(url, key)
    ```

- **Verificar uso de `any` em código Supabase**:
  - Procure: `as any`, `: any`, `Promise<any>` em arquivos que fazem queries
  - Cada `any` em código de banco de dados é um ponto cego — você não sabe o que está recebendo

- **Correção — gerar tipos**:
  ```bash
  # Instalar Supabase CLI se necessário
  npx supabase gen types typescript --project-id SEU_PROJECT_ID > src/types/supabase.ts
  ```
  Se não houver `SUPABASE_PROJECT_ID` configurado, oriente o usuário a rodar esse comando manualmente (requer login no Supabase CLI)

- **Substituir `any` por tipos corretos**:
  ```typescript
  // Antes (inseguro)
  const { data } = await supabase.from('posts').select('*')
  const post = data as any

  // Depois (seguro)
  import { Tables } from '@/types/supabase'
  const { data } = await supabase.from('posts').select('id, title, user_id')
  const post: Tables<'posts'> | null = data?.[0] ?? null
  ```

---

## Passo 3: Relatório final (task #28)

Após completar todas as tasks, você deve:

### 3.1 — Garantir que `security-report/` está no `.gitignore`

Antes de criar qualquer arquivo de relatório, verifique se `.gitignore` na raiz do projeto contém a entrada `security-report/`. Se não contiver, adicione-a. Isso garante que o relatório (que pode conter informações sensíveis sobre vulnerabilidades encontradas) nunca seja acidentalmente commitado.

```
# Adicionar ao .gitignore se ausente:
security-report/
```

### 3.2 — Criar o arquivo de relatório em `security-report/`

Crie a pasta `security-report/` na raiz do projeto (se não existir) e salve o relatório como:

```
security-report/audit-YYYY-MM-DD.md
```

Use a data atual no nome do arquivo (ex: `audit-2025-01-15.md`). Se já existir um arquivo com essa data, adicione sufixo `-2`, `-3`, etc.

### 3.3 — Estrutura obrigatória do relatório

O arquivo markdown deve seguir exatamente esta estrutura:

```markdown
# Relatório de Auditoria de Segurança
**Projeto:** [nome do projeto / pasta raiz]
**Data:** [data atual]
**Auditor:** Claude Security Auditor
**Stack identificada:** [ex: Next.js 14 App Router + Supabase + Vercel]

---

## 1. Estado do Sistema Identificado

### Estrutura do projeto
[Descreva o que foi encontrado: framework, versão, pastas principais, edge functions, migrations, etc.]

### Stack de tecnologias detectada
| Tecnologia | Versão | Observação |
|------------|--------|------------|
| [ex: Next.js] | [versão] | [obs] |
| [ex: React] | [versão] | [obs] |
| [ex: Supabase JS] | [versão] | [obs] |

### Superfície de ataque mapeada
[Liste: número de rotas, tabelas identificadas no schema/migrations, edge functions, buckets de storage, etc.]

---

## 2. Diagnóstico — Vulnerabilidades Encontradas

### Resumo executivo
| Prioridade | Total encontrado | Total corrigido | Requer ação manual |
|------------|-----------------|-----------------|-------------------|
| P0 — Crítico | X | X | X |
| P1 — Alto | X | X | X |
| P2 — Médio | X | X | X |
| **Total** | **X** | **X** | **X** |

### Detalhamento por categoria

Para cada uma das 27 categorias auditadas, registre uma entrada:

```
#### [#] [Nome da categoria] — [✅ Seguro | ❌ Vulnerável corrigido | ⚠️ Ação manual | ➖ Não aplicável]

**Risco:** [CRÍTICO / ALTO / MÉDIO]
**O que foi encontrado:** [descreva o problema encontrado, ou "nenhum problema identificado"]
**Arquivos/locais afetados:** [lista de arquivos ou "N/A"]
**Ação tomada:** [o que foi corrigido no código, ou "nenhuma ação necessária", ou "ver ação manual abaixo"]
```

---

## 3. Correções Aplicadas

[Liste aqui todas as mudanças efetivamente feitas nos arquivos do projeto. Para cada arquivo modificado:]

### `[caminho/do/arquivo]`
- **Problema:** [descrição]
- **Correção:** [o que foi alterado]

---

## 4. Ações Manuais Requeridas

[Esta seção é para tudo que requer intervenção humana — especialmente SQLs para executar no Supabase Dashboard]

### SQLs para executar no Supabase Dashboard

[Se houver, liste cada SQL com contexto de por que é necessário:]

#### [Tabela/contexto]
```sql
[SQL pronto para copiar e executar]
```

### Outras ações manuais
- [ ] [ex: Revogar e regenerar SUPABASE_SERVICE_ROLE_KEY pois foi encontrada exposta]
- [ ] [ex: Ativar MFA no Supabase Dashboard → Auth → MFA]
- [ ] [ex: Configurar Rate Limits em Dashboard → Auth → Rate Limits]

---

## 5. Pontuação de Segurança

| Dimensão | Antes | Depois | Observação |
|----------|-------|--------|------------|
| Secrets & Env vars | [nota /10] | [nota /10] | |
| Autenticação & Sessão | [nota /10] | [nota /10] | |
| Autorização & RLS | [nota /10] | [nota /10] | |
| Dependências | [nota /10] | [nota /10] | |
| Headers & CORS | [nota /10] | [nota /10] | |
| Frontend (XSS, sanitização) | [nota /10] | [nota /10] | |
| Infraestrutura (Storage, Functions) | [nota /10] | [nota /10] | |
| **Média geral** | **[X.X/10]** | **[X.X/10]** | |

---

## 6. Próximos Passos Recomendados

[Lista priorizada do que o time deve fazer após este relatório, além das ações manuais acima]

1. [ação mais urgente]
2. [segunda ação]
...

---

*Relatório gerado automaticamente pela skill `security-auditor`. Revise com seu time antes de compartilhar externamente.*
```

### 3.4 — Informar o usuário e solicitar autorização para Fase 2

Após salvar o arquivo, informe o usuário:
- O caminho exato do relatório gerado (`security-report/audit-YYYY-MM-DD.md`)
- Que a pasta já está protegida no `.gitignore`
- Um resumo de 3-4 linhas com os achados mais críticos

Então, **pare e pergunte ao usuário**:

> "✅ Auditoria e reparos concluídos. O relatório está em `security-report/audit-YYYY-MM-DD.md`.
>
> Posso executar a **Fase 2 — Verificação de integridade do app**? Ela vai testar se as correções aplicadas não quebraram nada: compilação TypeScript, build, lint e testes automatizados (se existirem). Isso pode levar alguns minutos.
>
> Responda **sim** para prosseguir ou **não** para encerrar aqui."

Só execute a Fase 2 se o usuário confirmar. Se disser não, encerre agradecendo.

---

## Fase 2 — Verificação de integridade do app (aguarda autorização)

Esta fase só começa após aprovação explícita do usuário. O objetivo é garantir que nenhuma das correções de segurança introduziu regressões — imports quebrados, erros de tipo, falhas de build, ou testes quebrando.

### Passo 4.1 — Detectar os scripts disponíveis

Antes de criar as tasks, leia `package.json` para identificar quais scripts existem:

```bash
cat package.json | grep -A 30 '"scripts"'
```

Mapeie o que está disponível:
| Verificação | Script provável | Obrigatório? |
|---|---|---|
| TypeScript | `tsc --noEmit` ou `type-check` | Sim se há `.ts`/`.tsx` |
| Build | `build` | Sim |
| Lint | `lint` | Sim |
| Testes unitários | `test` ou `test:unit` | Se existir |
| Testes e2e | `test:e2e` ou `cypress` ou `playwright` | Se existir |

### Passo 4.2 — Criar tasks de verificação e executar em paralelo

Crie uma task para cada verificação encontrada e execute-as. Se o ambiente suportar subagents, lance todos em paralelo — cada um rodando seu script independentemente. Isso reduz o tempo total de verificação de 5-10 minutos para o tempo do script mais lento.

```
Tasks a criar (apenas para os scripts identificados):
- [FASE2] TypeScript — verificar tipos: tsc --noEmit
- [FASE2] Build — verificar compilação: npm run build
- [FASE2] Lint — verificar estilo e erros: npm run lint
- [FASE2] Testes unitários — rodar suite: npm run test
- [FASE2] Testes e2e — rodar suite: npm run test:e2e
```

Para cada task, execute o script e capture:
- ✅ Passou sem erros
- ❌ Falhou — copie o erro completo
- ⚠️ Passou com warnings relevantes

### Passo 4.3 — Verificar especificamente os arquivos modificados

Além dos scripts gerais, faça uma verificação focada nos arquivos que foram alterados durante a auditoria. A ideia é detectar se alguma correção introduziu um erro que o build geral pode não capturar claramente.

Para cada arquivo modificado na auditoria:
```bash
# Verificar se o arquivo importa corretamente (sem erros de módulo)
npx tsc --noEmit --isolatedModules <caminho/do/arquivo>
```

Se algum arquivo modificado falhar isoladamente, reporte com o diff exato do que foi mudado.

### Passo 4.4 — Relatório da Fase 2

Ao final, apresente um resumo claro:

```
## Resultado da Fase 2 — Verificação de integridade

| Verificação | Status | Detalhe |
|---|---|---|
| TypeScript | ✅ Passou | 0 erros |
| Build | ✅ Passou | Concluído em 45s |
| Lint | ⚠️ 2 warnings | [descreva os warnings] |
| Testes unitários | ✅ 47/47 passaram | — |
| Testes e2e | ❌ 1 falhou | [cole o erro] |

### Arquivos modificados na auditoria verificados: X/X OK
```

Se alguma verificação falhou:
1. Analise se a falha está relacionada com as correções de segurança aplicadas
2. Se sim, corrija o problema (preserve a correção de segurança, ajuste o código ao redor)
3. Rode a verificação novamente para confirmar que passou
4. Documente no relatório de auditoria (`security-report/`) a falha e a correção adicional

Se tudo passou, informe o usuário com confiança de que o app está funcionando corretamente após os reparos de segurança.

---

## Dicas de busca por contexto do projeto

Ao iniciar, faça uma varredura rápida para entender a estrutura:

```
Glob: src/**/*.ts, src/**/*.tsx, *.config.*, vercel.json, .env*, supabase/migrations/**
```

Identifique:
- É Next.js App Router ou Pages Router?
- Usa Vite + React Router ou Next.js?
- Tem pasta `supabase/` com migrations?
- Tem pasta `supabase/functions/` (Edge Functions)?

Isso guia onde procurar cada vulnerabilidade.

## Arquivos de referência

Quando precisar de padrões de código completos, SQL avançado, ou checklists detalhadas, consulte:

| Arquivo | Conteúdo |
|---------|---------|
| `references/audit-details.md` | SQL e código TypeScript detalhado para todas as categorias; `getSession()` vs `getUser()`; `.or()` injection; Realtime avançado; Storage signed URLs |
| `references/advanced-rls.md` | Padrões multi-tenant (user_id, tenant_id via JWT, equipes/orgs); `(SELECT auth.uid())` performance; índices; event trigger auto-RLS; comportamentos silenciosos; RBAC via Custom Access Token Hook; `app_metadata` vs `user_metadata`; pgTap testing |
| `references/infrastructure.md` | OWASP Top 10 aplicado ao Supabase; CSP header completo; Dashboard hardening checklist; rate limits padrão do Auth; GitHub Actions security scan; schema exposure e permissões |
| `CHANGELOG.md` | Histórico completo de versões da skill — leia antes de fazer qualquer atualização futura |
