---
name: security-auditor
description: |
  Auditoria de segurança completa E correção automática para apps React + TypeScript + Supabase + Vercel, com checkup ampliado de LGPD, privacidade por design e guardrails modernos.
  Use esta skill SEMPRE que o usuário pedir para auditar segurança, checar vulnerabilidades, corrigir problemas de segurança, revisar RLS, verificar headers, ou qualquer tarefa de security review no projeto.
  Trigger phrases: "audita segurança", "verifica segurança", "checa vulnerabilidades", "revisa RLS", "security audit", "tem algum problema de segurança", "está seguro meu app", "corrija problemas de segurança", "security check", "auditoria completa", "audita LGPD", "verifica privacidade", "checkup de segurança".
  Auto-update triggers: "atualiza a skill", "update security-auditor", "baixa nova versão da skill", "instala update da skill", "atualiza o auditor de segurança". Quando acionado por esses triggers, execute APENAS o comando de atualização descrito no final deste arquivo, não inicie uma auditoria.
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

## Guardrails desta skill — comportamento seguro do auditor
Esta skill executa ações reais no projeto do usuário. Por isso, ela mesma deve seguir princípios de segurança:

- **Nunca execute comandos destrutivos sem confirmação**: se uma correção envolver deletar dados, revogar chaves ou alterar configurações de produção, pare e pergunte ao usuário
- **Não modifique segredos reais**: se encontrar `.env` com valores, NÃO os reescreva ou mova — apenas oriente o usuário a fazer isso manualmente
- **Proteja dados pessoais durante a auditoria**: não copie e-mails, CPFs ou outros PII para o relatório; anonimize ou referencie genericamente
- **Fail-safe**: se não tiver certeza sobre uma correção, registre como "ação manual recomendada" em vez de aplicar algo que possa quebrar o app
- **Transparência**: explique brevemente cada correção antes de aplicá-la; o usuário deve entender o que mudou
- **Verificação**: após cada correção, confirme que o problema foi resolvido e que não introduziu regressões
- **Sem alterações em CI/CD sem aviso**: workflows de GitHub Actions podem afetar deploys — proponha, não altere silenciosamente

## Modo Preventivo — se o usuário ainda está construindo o app

Se o usuário pediu a auditoria **antes** de codificar (ou no início do projeto), compartilhe estes prompt templates que ele pode usar com a IA para construir com segurança e privacidade desde o início:

### Template 1 — Segurança técnica
```
"Este sistema será submetido a um pentest profissional.
Aplique defesa em profundidade — cada camada deve ser
independentemente segura, mesmo que outra falhe.
Stack: React + TypeScript + Supabase + Vercel.
Regras obrigatórias:
- Toda lógica de permissão e cálculo financeiro fica no servidor (Edge Functions / Server Actions)
- Nunca confiar no frontend — toda validação ocorre no backend
- Transações financeiras e mudanças de estado crítico usam operações atômicas
- Somente usuários autorizados acessam recursos específicos (verificar IDOR)
- Limite máximo de tamanho em todos os campos de input"
```

### Template 2 — LGPD e privacidade por design
```
"Este app processará dados pessoais de usuários brasileiros e deve estar em conformidade com a LGPD desde o primeiro commit.
Aplique privacidade por design e por padrão:
- Colete apenas dados estritamente necessários (minimização)
- Obtenha e registre consentimento livre, específico e informado para cada finalidade
- Permita ao usuário acessar, corrigir, excluir e exportar seus dados (art. 18, LGPD)
- Implemente eliminação automática após o fim da finalidade ou pedido do titular
- Não armazene dados sensíveis sem necessidade e sem medidas técnicas extras
- Não envie PII para analytics, error trackers, logs ou third-parties sem anonimização/consentimento
- Prepare uma rotina de resposta a incidentes e notificação à ANPD"
```

A maior alavanca de segurança está no prompt — não no código. Uma instrução clara antes de começar evita reescritas custosas depois.

Se o app já está construído, prossiga com a auditoria abaixo.

---

## Passo 1: Criar o plano de trabalho com tasks

**IMEDIATAMENTE ao ser acionado**, use `TaskCreate` para criar tasks cobrindo TODAS as categorias abaixo. Crie cada task com sujeito descritivo e status inicial `pending`. Isso dá visibilidade ao usuário sobre o que será feito.

Crie as tasks nesta ordem de prioridade:

```
P0 — CRÍTICO (corrija hoje):
  1. [P0] Auditar e corrigir: Segredos & Variáveis de Ambiente
  1b. [P0] Auditar e corrigir: service_role — remover do projeto e migrar para Access Tokens temporários (7 dias)
  1c. [P0] Auditar e corrigir: Enumeração de usuários via mensagens de erro de autenticação
  1d. [P0] Auditar e corrigir: API keys e segredos de terceiros hardcoded no frontend
  2. [P0] Auditar e corrigir: Git & .gitignore (segredos commitados)
  3. [P0] Auditar e corrigir: Rotas privadas & autenticação
  3b. [P0] Auditar e corrigir: getSession() vs getUser() + CVE-2025-29927 middleware bypass
  3c. [P0] Auditar e corrigir: Server Actions e Route Handlers como endpoints públicos — re-autenticação obrigatória
  3d. [P0] Auditar e corrigir: Brute force protection — account lockout + CAPTCHA/Attack Protection no Supabase Auth
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
 11b. [P1] Auditar e corrigir: JWT algorithm lock — ES256/JWKS vs HS256 + algorithm confusion
 12. [P1] Auditar e corrigir: MFA — bypass e implementação correta
 13. [P1] Auditar e corrigir: Gerenciamento de sessão & logout
 13b. [P1] Auditar e corrigir: Session fixation — rotação de session ID pós-login e pós-sudo
 14. [P1] Auditar e corrigir: IDs sequenciais & IDOR
 15. [P1] Auditar e corrigir: Sanitização de retornos de API (over-fetching)
 16. [P1] Auditar e corrigir: Criptografia de dados sensíveis
 17. [P1] Auditar e corrigir: CORS & Security Headers (vercel.json)
 17b. [P1] Auditar e corrigir: Cross-Origin Isolation headers — COEP, COOP, CORP
 18. [P1] Auditar e corrigir: Rate limiting & proteção anti-brute-force
 18b. [P1] Auditar e corrigir: Limite máximo de tamanho para todos os inputs (DoS prevenção)
 18c. [P1] Auditar e corrigir: Testes automatizados de segurança (gerar suite TDD)
 19. [P1] Auditar e corrigir: Injeção SQL, XSS & Prototype Pollution
 19b. [P1] Auditar e corrigir: ReDoS — regex com quantificadores aninhados em validações server-side
 20. [P1] Auditar e corrigir: Supabase Realtime & subscriptions
 20b. [P1] Auditar e corrigir: Arquitetura cliente-servidor — lógica sensível exposta no frontend
 20c. [P1] Auditar e corrigir: .or() PostgREST injection — interpolação de input no método .or()
 20d. [P1] Auditar e corrigir: Realtime canais privados + RLS na realtime.messages
 20e. [P1] Auditar e corrigir: Zod .strict() para mass assignment + noUncheckedIndexedAccess no tsconfig
 20f. [P1] Auditar e corrigir: Data Access Layer + server-only package + React Taint APIs
 20g. [P1] Auditar e corrigir: CSRF em Route Handlers — verificar origin header em mutations
 20h. [P1] Auditar e corrigir: Open Redirect — validar redirectTo e next params
 20i. [P1] Auditar e corrigir: Password hashing seguro — bcrypt/Argon2id em auth customizada
 20j. [P1] Auditar e corrigir: Error handling seguro — não expor stack traces, fail-safe defaults

P2 — MÉDIO (próximo sprint):
 21. [P2] Auditar e corrigir: Upload de arquivos — validação MIME & tamanho
 22. [P2] Auditar e corrigir: CSP & Subresource Integrity (supply chain)
 22b. [P2] Auditar e corrigir: Supply chain security — lockfile, npm ci, verificação de integridade
 23. [P2] Auditar e corrigir: console.log em produção & source maps
 24. [P2] Auditar e corrigir: Supabase Vault & rotação de chaves
 25. [P2] Auditar e corrigir: Lógica de negócio & race conditions
 26. [P2] Auditar e corrigir: LGPD/GDPR — direitos do titular, consentimento, retenção, DPO, DPIA e notificação de incidentes
 27. [P2] Auditar e corrigir: Logging, monitoramento & alertas de segurança
 27b. [P2] Auditar e corrigir: TypeScript types do Supabase e eliminação de `any`
 27c. [P2] Auditar e corrigir: Schema exposure — schema private + permissões desnecessárias de anon
 27d. [P2] Auditar e corrigir: PII detection & data classification — mapear e proteger dados pessoais
 27e. [P2] Auditar e corrigir: Backup, disaster recovery & RTO/RPO
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

#### 1c. Enumeração de usuários via mensagens de erro
A IA frequentemente gera mensagens de erro úteis para o desenvolvedor — mas que revelam informação ao atacante. Mensagens como "E-mail não encontrado" ou "Senha incorreta" permitem que um atacante saiba quais e-mails estão cadastrados no sistema (enumeração de usuários).

- **Procure** em formulários de login, registro e recuperação de senha:
  ```bash
  grep -rn "não encontrado\|not found\|email.*inexistente\|usuário.*não existe\|invalid email\|wrong password\|senha incorreta" \
    src/ app/ --include="*.ts" --include="*.tsx"
  ```
- **Risco**: um atacante pode automatizar tentativas com listas de e-mails e saber exatamente quais estão cadastrados — depois usa isso para phishing direcionado ou credential stuffing
- **Correção**: substituir todas as mensagens de erro de autenticação por uma mensagem genérica:
  ```typescript
  // ❌ Perigoso — revela se o e-mail existe
  if (!user) return { error: "E-mail não encontrado" }
  if (!passwordMatch) return { error: "Senha incorreta" }

  // ✅ Seguro — mesma mensagem para qualquer falha
  return { error: "Credenciais inválidas. Verifique seu e-mail e senha." }
  ```
- **Também verificar**: endpoints de recuperação de senha — não revelar se o e-mail está cadastrado. Retornar sempre "Se esse e-mail estiver cadastrado, você receberá um link em breve."
- Para padrões detalhados, veja `references/audit-details.md` → seção "Enumeração de usuários"

#### 1d. API keys e segredos de terceiros hardcoded no frontend
Além da `SUPABASE_SERVICE_ROLE_KEY`, qualquer chave de API de terceiros (OpenAI, Stripe, Google Maps, SendGrid, etc.) que apareça em código client-side pode ser extraída do bundle JavaScript e usada por atacantes — mesmo que seja uma chave "pública".

- **Procure**: strings hardcoded em arquivos `.ts/.tsx` fora de server-only:
  ```bash
  grep -rnE "(sk-[a-zA-Z0-9]{20,}|pk_live_[a-zA-Z0-9]{20,}|AIza[0-9A-Za-z_-]{35}|SG\.[a-zA-Z0-9_-]{22,})" \
    src/ app/ --include="*.ts" --include="*.tsx"
  ```
- **Risco**: uso indevido de quotas, exfiltração de dados, custos inesperados e vazamento de dados dos usuários
- **Correção**:
  - Mover chamadas a APIs de terceiros para Edge Functions / Server Actions
  - Se uma chave realmente precisa estar no frontend (ex: Google Maps), restrinja domínios no dashboard do provedor e rotacione periodicamente
  - Nunca commitar valores reais — usar `.env.example` sem valores
- Para padrões detalhados, veja `references/audit-details.md` → seção "Segredos & Variáveis de Ambiente"

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

#### 3c. Server Actions e Route Handlers como endpoints públicos [P0]
O middleware do Next.js protege páginas — mas Server Actions e Route Handlers são endpoints HTTP independentes. Um usuário mal-intencionado pode chamá-los diretamente, bypassando completamente o middleware.

- **Procure**: arquivos com `'use server'` sem `auth.getUser()` no mesmo escopo:
  ```bash
  grep -rn "'use server'" app/ src/ --include="*.ts" --include="*.tsx" -l
  # Para cada arquivo encontrado, verificar se chama auth.getUser()
  grep -rn "auth.getUser\|getUser()" app/ src/ --include="*.ts" --include="*.tsx"
  ```
- **Procure**: Route Handlers com mutações sem auth check:
  ```bash
  grep -rn "export.*POST\|export.*PUT\|export.*DELETE\|export.*PATCH" app/ --include="route.ts"
  ```
- **Correção** — cada Server Action e Route Handler deve verificar auth independentemente:
  ```typescript
  // ✅ Pattern obrigatório em cada Server Action
  'use server'
  import { createClient } from '@/lib/supabase/server'

  export async function sensitiveAction(formData: FormData) {
    const supabase = createClient()
    const { data: { user }, error } = await supabase.auth.getUser()
    if (error || !user) throw new Error('Unauthorized')
    // lógica só executa após verificar auth
  }
  ```
- **Risco**: um atacante pode descobrir os nomes das Server Actions via source maps e chamá-las diretamente com `fetch('/path?_action=xxx')`
- Para padrões completos, veja `references/audit-details.md` → seção "Server Actions como endpoints públicos"

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

#### 3d. Brute force protection — account lockout + CAPTCHA/Attack Protection
O Supabase Auth possui rate limits padrão, mas eles são genéricos. Apps em produção precisam de proteção explícita contra brute force em login, signup e recuperação de senha.

- **Verificar no Dashboard**: Auth → Attack Protection → habilitar CAPTCHA (hCaptcha/Turnstile)
- **Verificar rate limits customizados**: Auth → Rate Limits
  - Signup: máximo 4/hora por IP
  - Login: máximo 10/hora por IP (ou mais restritivo)
  - Password recovery: máximo 3/hora
- **Se houver auth customizada**, verificar account lockout após N tentativas falhas:
  ```sql
  -- Tabela de tentativas falhas
  CREATE TABLE IF NOT EXISTS public.auth_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    ip TEXT,
    attempted_at TIMESTAMPTZ DEFAULT now()
  );
  ```
- **Correção**: implementar lockout temporário (15-30 min) após 5 tentativas falhas, ou usar Upstash Ratelimit por e-mail/IP
- Para padrões detalhados, veja `references/audit-details.md` → seção "Rate limiting"

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
- **CVEs críticos a verificar**:

| CVE / ID | Pacote | CVSS | Descrição | Correção |
|----------|--------|------|-----------|---------|
| CVE-2025-55182 | react 19.0.0–19.2.3 | 10.0 | RCE via RSC payload malformado (React2Shell) | `npm i react@latest react-dom@latest` |
| CVE-2025-66478 | next < 15.1.9 ou < 16.0.7 | 10.0 | RCE via deserialização insegura de payload RSC (herdado do React) | Atualizar Next.js |
| CVE-2025-55183 | react / next | 8.5 | Exposição de código-fonte via RSC | Atualizar React/Next.js |
| CVE-2025-55184 | react / next | 7.5 | DoS via payload RSC malformado | Atualizar React/Next.js |
| CVE-2025-67779 | react / next | 7.5 | Expansão da classe DoS do CVE-2025-55184 | Atualizar React/Next.js |
| CVE-2025-48757 | apps Supabase (padrão Lovable) | 10.0 | Exposição total de dados por RLS desabilitado/incorreto | Habilitar RLS em todas as tabelas com dados de usuário |
| CVE-2025-29927 | next < 14.2.25 ou < 15.2.3 | 9.1 | Middleware bypass via `x-middleware-subrequest` | Atualizar Next.js |
| CVE-2024-56332 | next < 14.2.21 | 9.1 | RCE via Server-Side Request Forgery em RSC | Atualizar Next.js |
| CVE-2024-34351 | next < 14.1.1 | 7.5 | SSRF via Host header em Route Handlers | Atualizar Next.js |
| CVE-2024-46982 | next < 14.2.10 | 7.5 | Cache poisoning via crafted response | Atualizar Next.js |
| GHSA-3529 | GoTrue (self-hosted) | alto | Email link poisoning — URLs em emails de auth manipuláveis | Atualizar GoTrue; não aplicável ao Supabase cloud |
| jsonwebtoken < 9.0 | jsonwebtoken | alto | Algorithm confusion — aceita `alg: none` | `npm i jsonwebtoken@latest` |
| react-router < 7.5.2 | react-router | alto | DoS e XSS armazenado | `npm i react-router@latest` |

- **Correção**: `npm audit fix` para patches automáticos; updates manuais para breaking changes
- **Nota GHSA-3529**: só relevante para instâncias self-hosted do Supabase Auth (GoTrue). No Supabase cloud, já está corrigido.

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

**Cláusula `TO authenticated` obrigatória:**
Policies sem `TO` se aplicam a todos os roles, incluindo `anon`. Verificar se todas as policies têm o role correto:
```sql
-- Verificar policies sem cláusula TO (se aplicam a anon também):
SELECT tablename, policyname, roles
FROM pg_policies
WHERE schemaname = 'public'
  AND (roles = '{}' OR roles IS NULL OR roles::text = '{=}');
-- Resultado vazio é OK se esperado, mas policies de dados de usuário devem ter TO authenticated
```

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

#### 11b. JWT algorithm lock — ES256/JWKS vs HS256
O Supabase usa HS256 por padrão para assinar JWTs, mas ES256 (assimétrico) é mais robusto: a chave privada fica apenas no servidor Auth, enquanto verificadores usam apenas a chave pública — eliminando riscos de vazamento da secret de assinatura.

- **Verificar algoritmo no Dashboard**: Project Settings → API → JWT Settings → Algorithm
- **Para projetos de alta segurança**: trocar de HS256 para ES256 (requer Supabase Pro)
- **Verificar** se o projeto usa o pacote `jsonwebtoken` diretamente:
  ```bash
  grep -rn "jwt.verify\|jwt.decode\|jsonwebtoken" src/ app/ --include="*.ts"
  ```
  - `jsonwebtoken < 9.0.0`: vulnerável a algorithm confusion (CVE registrado) — aceita `alg: none`
  - **Correção**: `npm install jsonwebtoken@latest`
- **Nunca faça `jwt.decode()` sem `jwt.verify()`** — decode não verifica a assinatura
- Para self-hosted Supabase: verificar JWKS endpoint (`/auth/v1/.well-known/jwks.json`) e rotação de chaves
- Para detalhes, veja `references/audit-details.md` → seção "JWT algorithm lock"

#### 12. MFA bypass
- **SQL para verificar policies que deveriam exigir MFA**:
  ```sql
  SELECT policyname, qual FROM pg_policies
  WHERE schemaname = 'public' AND qual NOT ILIKE '%aal2%';
  ```
- **Para tabelas sensíveis**, adicionar verificação AAL com `AS RESTRICTIVE` (a política RESTRICTIVE é AND com todas as outras — não pode ser bypassada por outras policies PERMISSIVE):
  ```sql
  -- RESTRICTIVE: aplica em cima de todas as outras policies (lógica AND)
  CREATE POLICY "enforce_mfa" ON tabela_sensivel
    AS RESTRICTIVE FOR ALL TO authenticated
    USING ((auth.jwt()->>'aal') = 'aal2');

  -- PERMISSIVE: política normal de propriedade (lógica OR com outras PERMISSIVE)
  CREATE POLICY "users_own_data" ON tabela_sensivel
    FOR ALL TO authenticated
    USING ((SELECT auth.uid()) = user_id)
    WITH CHECK ((SELECT auth.uid()) = user_id);
  ```
  A combinação garante que o usuário precisa de MFA **E** ser dono do recurso.

#### 13. Sessão & logout
- **Procure**: `localStorage.setItem` com tokens — preferir cookies HttpOnly
- **Verificar**: fluxo de logout chama `supabase.auth.signOut()` e não apenas limpa localStorage
- **Procure**: falta de logout automático por inatividade em apps com dados financeiros/saúde

#### 13b. Session fixation — rotação de session ID pós-login
Session fixation ocorre quando um atacante conhece o session ID antes do login (ex: via XSS ou sniffing) e depois usa essa sessão já autenticada. A defesa é rotacionar o session ID imediatamente após qualquer elevação de privilégio.

- **Procure**: fluxos de auth customizada que não chamam `refreshSession()` após login:
  ```bash
  grep -rn "signInWithPassword\|signUp\|signInWithOtp" src/ app/ --include="*.ts" --include="*.tsx"
  ```
- **Correção**: após login bem-sucedido ou após qualquer "sudo" (re-confirmação de senha para operações críticas):
  ```typescript
  // Após signIn bem-sucedido em auth customizada
  const { data: signInData } = await supabase.auth.signInWithPassword({ email, password })
  if (signInData.session) {
    // Rotacionar session ID — invalida tokens antigos
    await supabase.auth.refreshSession()
  }
  ```
- O Supabase Auth gerenciado faz isso automaticamente para fluxos nativos. O risco é maior em auth customizada (Edge Functions) ou em fluxos "sudo" que reconfirmam credenciais sem trocar o token
- **Verificar**: operações críticas (troca de email, senha, delete de conta) exigem reconfirmação de senha antes de executar?

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

#### 17b. Cross-Origin Isolation headers
Headers Cross-Origin protegem contra ataques Spectre (side-channel via SharedArrayBuffer), XS-Leaks e timing attacks cross-origin. Especialmente relevante para apps que processam dados sensíveis.

- **Procure**: `vercel.json` ou `next.config.*` — os três headers devem estar presentes
- **Adicionar ao vercel.json** (para apps que precisam de isolamento completo):
  ```json
  { "key": "Cross-Origin-Embedder-Policy", "value": "require-corp" },
  { "key": "Cross-Origin-Opener-Policy", "value": "same-origin" },
  { "key": "Cross-Origin-Resource-Policy", "value": "same-origin" }
  ```
- **Nota**: COEP `require-corp` pode quebrar recursos externos (CDNs, imagens, iframes de terceiros). Se houver recursos cross-origin necessários, use `credentialless` em vez de `require-corp`, ou adicione `crossorigin="anonymous"` nos recursos afetados.
- **Verificar COOP em apps com OAuth**: `same-origin` pode quebrar popups OAuth (Google, GitHub). Nesses casos, usar `same-origin-allow-popups`.
- Para lista completa de Security Headers, veja `references/infrastructure.md` → seção "CSP"

#### 18. Rate limiting
- **Procure**: endpoints de login, signup, password reset sem rate limiting
- **Verificar**: Supabase Dashboard → Authentication → Rate Limits estão configurados
- **Diferentes limites por endpoint**: login deve ter limite mais restritivo (5 tentativas/minuto por IP) do que busca (100/minuto)
- **Correção com Upstash** (se não houver rate limiting):
  ```typescript
  // Em middleware.ts ou Edge Function
  import { Ratelimit } from "@upstash/ratelimit";
  import { Redis } from "@upstash/redis";
  const ratelimit = new Ratelimit({ redis: Redis.fromEnv(), limiter: Ratelimit.slidingWindow(10, "10 s") });
  const { success } = await ratelimit.limit(ip);
  if (!success) return new Response("Too Many Requests", { status: 429 });
  ```
- **Honeypots (opcional, alta eficácia)**: adicionar rotas falsas que retornam dados plausíveis mas inúteis para atacantes que fazem scanning automático. Um atacante que acerta a rota honeypot pode ser automaticamente bloqueado.
- Para detalhes de configuração de limites por endpoint, veja `references/audit-details.md` → seção "Rate limiting"

#### 18b. Limite máximo de tamanho para todos os inputs
Inputs sem limite de tamanho são um vetor de DoS — um atacante pode enviar campos de 10MB repetidamente, consumindo memória, processamento de banco e armazenamento.

- **Procure**: campos de formulário e API sem validação de tamanho máximo:
  ```bash
  # Procurar schemas Zod sem .max()
  grep -rn "z\.string()\." src/ app/ --include="*.ts" --include="*.tsx" | grep -v "\.max("
  ```
- **Risco**: campos de texto ilimitados podem causar degradação de performance e gastos inesperados com storage
- **Correção — Zod no servidor**:
  ```typescript
  const schema = z.object({
    name: z.string().max(100),        // nome
    bio: z.string().max(500),         // bio
    message: z.string().max(2000),    // mensagem longa
    email: z.string().email().max(254), // email (RFC 5321)
    slug: z.string().max(100).regex(/^[a-z0-9-]+$/),
  })
  ```
- **Correção — constraint no banco** (defesa em profundidade):
  ```sql
  ALTER TABLE public.profiles ADD CONSTRAINT bio_max_length CHECK (length(bio) <= 500);
  ALTER TABLE public.messages ADD CONSTRAINT content_max_length CHECK (length(content) <= 2000);
  ```
- Campos críticos: `bio`, `description`, `comment`, `message`, `title`, `name`, `address`
- Para padrões completos, veja `references/audit-details.md` → seção "Input size limits"

#### 18c. Testes automatizados de segurança
A IA que construiu o app pode também gerar os testes de segurança — e isso é uma das práticas mais eficazes para garantir que novas features não introduzam regressões de segurança.

Se o projeto tem uma suíte de testes, verifique se há cobertura para cenários de segurança. Se não houver, gere os testes essenciais:

- **Verificar se existe** `*.test.ts`, `*.spec.ts`, `__tests__/`:
  ```bash
  find . -name "*.test.ts" -o -name "*.spec.ts" | grep -v node_modules | head -20
  ```
- **Cenários de segurança que devem ter teste**:
  - Acesso a recurso de outro usuário retorna 403 (IDOR)
  - Endpoint sem autenticação retorna 401
  - Input com caracteres especiais `<script>`, `'; DROP TABLE`, `../../../etc/passwd` é rejeitado
  - Rate limiting bloqueia após N tentativas
  - Upload de arquivo com extensão .exe ou .php é rejeitado
- **Gerar teste de IDOR** (exemplo Vitest/Jest):
  ```typescript
  it('should not allow user A to access user B resources', async () => {
    const userAToken = await signIn(userA)
    const userBResourceId = await createResource(userB)
    const response = await fetch(`/api/resources/${userBResourceId}`, {
      headers: { Authorization: `Bearer ${userAToken}` }
    })
    expect(response.status).toBe(403)
  })
  ```
- Se não há framework de testes configurado, **reporte apenas** e liste os cenários que deveriam ser cobertos — não instale um framework de testes sem orientação do usuário

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

#### 19b. ReDoS — regex com quantificadores aninhados
Regular Expression Denial of Service ocorre quando uma regex com backtracking catastrófico é avaliada contra um input longo — o tempo de processamento cresce exponencialmente. Um atacante envia 10KB de input cuidadosamente construído e trava a thread Node.js por segundos.

- **Procure**: regex com quantificadores aninhados em código server-side:
  ```bash
  grep -rn "\.test(\|\.match(\|\.replace(" src/ app/ --include="*.ts" | grep -v "//\|test\."
  ```
  Padrões vulneráveis a buscar:
  - `/(a+)+/` — quantificador dentro de grupo com quantificador
  - `/([a-z]+)*$/` — grupo repetível no final sem âncora
  - `/(.*)*$/` — qualquer nesting de `.*` com `*`

- **Correção**: usar Zod para validações em vez de regex manual:
  ```typescript
  // ❌ Regex vulnerável — DoS com input: "aaaaaaaaaaaaaaaaaaaaaa!"
  const emailRegex = /^([a-zA-Z0-9])+([a-zA-Z0-9\._-])*@([a-zA-Z0-9_-])+([a-zA-Z0-9\._-]+)+$/

  // ✅ Delegar para Zod (usa regex linear internamente)
  const schema = z.object({
    email: z.string().email().max(254),
    slug: z.string().regex(/^[a-z0-9-]{1,100}$/)  // quantificadores com limite explícito
  })
  ```
- **Regra**: qualquer regex server-side deve ter limites explícitos (`{1,100}`, não `+` ou `*` sozinhos) ou usar Zod
- O limite de tamanho do input (task 18b) é a primeira linha de defesa — um input de 254 chars máximo limita muito o impacto de ReDoS

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

#### 20e. Zod `.strict()` para mass assignment + `noUncheckedIndexedAccess`
Dois problemas independentes que a IA frequentemente ignora na geração de código.

**Mass assignment via Zod sem `.strict()`:**
- **Procure**: schemas Zod sem `.strict()` em Server Actions e Route Handlers que passam dados diretamente para o banco:
  ```bash
  grep -rn "z\.object({" src/ app/ --include="*.ts" --include="*.tsx" | grep -v "\.strict()"
  ```
- **Risco**: um usuário pode enviar `{ name: "João", role: "admin" }` e o campo `role` vai silenciosamente para o `INSERT` se não for explicitamente bloqueado
- **Correção**: adicionar `.strict()` em todos os schemas que processam input do usuário:
  ```typescript
  // ❌ Aceita campos extras silenciosamente
  const schema = z.object({ name: z.string(), email: z.string().email() })

  // ✅ Rejeita qualquer campo não declarado com erro de validação
  const schema = z.object({ name: z.string(), email: z.string().email() }).strict()
  ```

**`noUncheckedIndexedAccess` no tsconfig:**
- **Verificar**: `tsconfig.json` tem `"noUncheckedIndexedAccess": true`?
- **Risco**: `data[0].field` pode ser `undefined` se o array estiver vazio — TypeScript sem essa flag não avisa, gerando crashes em runtime
- **Correção**: adicionar ao `tsconfig.json`:
  ```json
  { "compilerOptions": { "noUncheckedIndexedAccess": true } }
  ```
  Após adicionar, o TypeScript vai apontar todos os locais que precisam de `?? fallback` — corrija-os.

#### 20f. Data Access Layer + `server-only` + React Taint APIs
Separação de responsabilidades no nível de módulo — garante que código de acesso a banco nunca vaze para o bundle do browser.

- **Verificar**: existe uma pasta `src/lib/data-access/` ou `src/dal/` com funções de banco separadas de componentes?
- **`server-only` package**: adicionar em arquivos que acessam o banco:
  ```typescript
  // src/lib/data-access/users.ts
  import 'server-only'  // ← erro em build-time se importado no cliente
  import { createClient } from '@/lib/supabase/server'

  export async function getUserById(id: string) {
    const supabase = createClient()
    const { data } = await supabase.from('users').select('id, name, email').eq('id', id).single()
    return data
  }
  ```
  Se `server-only` não estiver instalado: `npm install server-only`

- **React Taint APIs** (React 19+ / Next.js 14+): marca objetos que nunca devem ser serializados para o cliente:
  ```typescript
  import { experimental_taintObjectReference, experimental_taintUniqueValue } from 'react'

  // Marcar objeto inteiro como "nunca enviar ao cliente"
  experimental_taintObjectReference('Não passar credenciais ao cliente', userWithPassword)

  // Marcar valor específico (tokens, chaves)
  experimental_taintUniqueValue('Não expor token de sessão', cache, sessionToken)
  ```
- **Verificar se ativo**: `next.config.ts` tem `experimental: { taint: true }`?
- Para padrões completos, veja `references/audit-details.md` → seção "Data Access Layer"

#### 20g. CSRF em Route Handlers
Route Handlers POST/PUT/DELETE sem verificação de origem são vulneráveis a Cross-Site Request Forgery — um site malicioso pode fazer o browser do usuário autenticado disparar requests para sua API.

- **Procure**: Route Handlers com mutações:
  ```bash
  grep -rn "export.*POST\|export.*PUT\|export.*DELETE\|export.*PATCH" app/ --include="route.ts" -l
  ```
- **Para cada arquivo encontrado**, verificar se há validação de `origin` ou `referer`:
  ```typescript
  // ✅ Verificar origin em mutations
  export async function POST(req: Request) {
    const origin = req.headers.get('origin')
    const host = req.headers.get('host')
    if (!origin || !origin.includes(host ?? '')) {
      return Response.json({ error: 'Forbidden' }, { status: 403 })
    }
    // ...
  }
  ```
- **Nota**: Server Actions do Next.js têm proteção CSRF built-in desde Next.js 14. O risco é maior em Route Handlers criados manualmente.
- **Alternativa moderna**: usar `SameSite=Strict` nos cookies de session (Supabase Auth já faz isso)

#### 20h. Open Redirect — validar parâmetros de redirecionamento
Parâmetros como `?next=`, `?redirect=`, `?returnTo=` são vetores clássicos de phishing — um atacante envia `https://seuapp.com/login?next=https://phishing.com` e após o login, o usuário é redirecionado para o site malicioso.

- **Procure**: redirecionamentos com parâmetros da URL:
  ```bash
  grep -rn "redirect(\|router\.push(\|window\.location" src/ app/ --include="*.ts" --include="*.tsx" | grep -i "searchParams\|params\|query\|req\."
  ```
- **Correção**: sempre validar que o destino é um path relativo ou domínio autorizado:
  ```typescript
  // ❌ Redireciona para qualquer URL sem validação
  const next = searchParams.get('next') ?? '/'
  redirect(next)

  // ✅ Só aceita paths relativos (não URLs absolutas)
  const rawNext = searchParams.get('next') ?? '/'
  // Rejeita URLs absolutas: http://, https://, // (protocol-relative)
  const safePath = /^\/[^/\\]/.test(rawNext) ? rawNext : '/'
  redirect(safePath)
  ```
- **Verificar**: Supabase Auth `redirectTo` em `signInWithOAuth` — usar `process.env.NEXT_PUBLIC_APP_URL` como base, nunca valor vindo do cliente

#### 20i. Password hashing seguro — em auth customizada
Se o projeto não usa Supabase Auth e implementa autenticação própria, o hashing de senhas é o ponto mais crítico. Senhas em texto plano, MD5, SHA-1 ou SHA-256 sem salt são inaceitáveis.

- **Procure**:
  ```bash
  grep -rnE "(md5|sha1|sha256|bcrypt|argon2|pbkdf2|hashPassword|compare)" \
    src/ app/ --include="*.ts" --include="*.tsx"
  ```
- **Regra**: preferir **Argon2id** (OWASP 2023 recommendation) ou **bcrypt** com custo ≥ 12. Nunca usar MD5/SHA-1/SHA-256 para senhas.
- **Correção**:
  ```typescript
  import { hash, verify } from 'argon2'
  const passwordHash = await hash(password)
  const isValid = await verify(passwordHash, inputPassword)
  ```
- **Sempre** usar salt automático do algoritmo — nunca salt fixo
- Para padrões detalhados, veja `references/audit-details.md` → seção "Password hashing"

#### 20j. Error handling seguro — fail-safe e não exposição de detalhes
Aplicações que "falham aberto" (fail-open) ou expõem stack traces, nomes de tabelas e estrutura interna em mensagens de erro dão informação valiosa a atacantes. OWASP 2025 incluiu "Mishandling of Exceptional Conditions" no Top 10.

- **Procure**: envio de `error.stack` ou objetos de erro completos para o cliente:
  ```bash
  grep -rn "error\.stack\|error\.message\|JSON\.stringify(error\|console\.error(error" \
    src/ app/ --include="*.ts" --include="*.tsx"
  ```
- **Regra de ouro**: em produção, retorne mensagens genéricas ao cliente e logue detalhes apenas no servidor:
  ```typescript
  // ❌ Expor detalhes internos
  return Response.json({ error: err.message, stack: err.stack }, { status: 500 })

  // ✅ Genérico para o cliente, detalhado no log
  console.error('[UNEXPECTED_ERROR]', err)
  return Response.json({ error: 'Internal server error' }, { status: 500 })
  ```
- **Fail-safe**: se a verificação de auth falhar (banco indisponível, JWT inválido), o padrão deve ser **negar** o acesso, não permitir
- **Verificar**: handlers que fazem `if (user) { permitir }` sem `else { negar }` explícito
- Para padrões detalhados, veja `references/audit-details.md` → seção "Error handling seguro"

---

### P2 — Segurança média

#### 21. Upload de arquivos
- **SQL**: verificar `allowed_mime_types` e `file_size_limit` nos buckets (já coberto em #7)
- **Procure no frontend**: validação apenas por extensão (inseguro) vs. magic bytes
- **Tipos NUNCA aceitar**: `.svg`, `.html`, `.php`, `.exe`, `.sh`
- **Correção**: gerar nome UUID para arquivos `${crypto.randomUUID()}.${ext}` e usar signed URLs
- **Risco extra — URLs externas como IP trackers**: se o app permite que usuários insiram URLs de imagem (avatar, banner, etc.) sem validação de domínio, um atacante pode inserir uma URL de servidor controlado por ele. Quando outros usuários carregarem a página, seus IPs serão capturados pelo servidor do atacante.
  ```typescript
  // Verificar: o app aceita URLs externas para imagens de perfil?
  grep -rn "avatar_url\|image_url\|banner_url\|photo_url" src/ app/ --include="*.ts" --include="*.tsx"
  // Correção: validar que a URL pertence ao seu domínio ou ao Supabase Storage
  const isValidImageUrl = (url: string) => {
    const allowed = ['seu-projeto.supabase.co', 'seu-dominio.com']
    try {
      const parsed = new URL(url)
      return allowed.some(domain => parsed.hostname.endsWith(domain))
    } catch { return false }
  }
  ```
- Para validação de magic bytes e padrões detalhados, veja `references/audit-details.md` → seção "Upload de arquivos"

#### 22. CSP & SRI
- **Procure**: `<script src="https://...">` sem atributo `integrity` no HTML/layout
- **Procure em next.config.ts**: `experimental: { sri: { algorithm: 'sha256' } }`
- **Correção**: adicionar SRI hashes ou bundlar dependências localmente (npm install)

#### 22b. Supply chain security — lockfile, npm ci e verificação de integridade
OWASP Top 10 2025 elevou "Software Supply Chain Failures" para A03. Apps modernos dependem de centenas de pacotes npm — um pacote comprometido ou um lockfile desatualizado pode introduzir backdoors e vulnerabilidades conhecidas.

- **Verificar**: `package-lock.json` ou `yarn.lock`/`pnpm-lock.yaml` está commitado?
- **Verificar**: CI/CD usa `npm ci` em vez de `npm install`? (`npm install` pode atualizar versões sem querer)
- **Verificar**: configuração do `.npmrc` para não instalar pacotes sem assinatura:
  ```ini
  # .npmrc
  engine-strict=true
  package-lock=true
  ```
- **Procure**: scripts `postinstall` suspeitos em dependências:
  ```bash
  grep -rn "postinstall" node_modules/*/package.json 2>/dev/null | head -20
  ```
- **Correção**: usar `npm audit --production` no CI, pinar versões no `package.json` e manter lockfile atualizado
- Para padrões detalhados, veja `references/audit-details.md` → seção "Supply chain security"

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
A IA erra mais nesta categoria do que em qualquer outra. Fluxos de negócio complexos têm combinações não-óbvias que criam brechas — e a IA só cobre os casos que você descreve explicitamente.

- **Procure**: cálculo de preço no frontend (nunca confiar no cliente)
- **Procure**: ausência de idempotency keys em operações de pagamento
- **Questione estes fluxos absurdos** — se existirem no app, teste cada um:
  - Um usuário compra → solicita reembolso → a comissão de afiliado ainda é creditada?
  - Um usuário pode submeter o mesmo formulário duas vezes simultaneamente e ganhar o benefício duas vezes (race condition de estado)?
  - Existe algum fluxo onde combinar ações legítimas resulta em ganho de recurso infinito? (ex: criar → deletar → recriar com bônus novamente)
  - Um usuário pode usar um cupom de desconto enquanto simultaneamente inicia outro checkout com o mesmo cupom?
- **Race condition — padrão vulnerável vs seguro**:
  ```typescript
  // ❌ Vulnerável: duas operações separadas — janela de exploração entre elas
  const balance = await getBalance(userId)    // lê saldo
  if (balance >= amount) {
    await deductBalance(userId, amount)       // debita — race condition aqui
  }

  // ✅ Seguro: verificar e agir na mesma operação atômica
  await supabase.rpc('deduct_balance_atomic', { user_id: userId, amount })
  ```
  ```sql
  -- Função atômica com lock e verificação dentro da transaction
  CREATE OR REPLACE FUNCTION deduct_balance_atomic(user_id uuid, amount numeric)
  RETURNS void LANGUAGE plpgsql AS $$
  BEGIN
    UPDATE wallets
    SET balance = balance - amount
    WHERE id = user_id AND balance >= amount; -- verificação + débito em uma operação
    IF NOT FOUND THEN
      RAISE EXCEPTION 'Saldo insuficiente';
    END IF;
  END;
  $$;
  ```
- **Correção para duplicatas** (idempotency):
  ```sql
  INSERT INTO user_bonuses (user_id, bonus_type)
  VALUES (auth.uid(), 'welcome')
  ON CONFLICT (user_id, bonus_type) DO NOTHING;
  ```
- Para padrões detalhados, veja `references/audit-details.md` → seção "Race conditions"

#### 26. LGPD/GDPR — privacidade por design e direitos do titular
A LGPD (Lei Geral de Proteção de Dados) estabelece obrigações técnicas e organizacionais que vão muito além de "ter um botão de deletar conta". Esta task cobre os principais requisitos aplicáveis a apps React + Supabase.

**Direitos do titular (art. 18, LGPD) — checklist de implementação:**

| Direito | O que verificar no app | Implementação típica |
|---------|----------------------|---------------------|
| Confirmação e acesso | Existe endpoint/página onde o usuário vê seus dados? | `/account/data` com exportação JSON |
| Correção | Usuário pode editar dados pessoais? | Formulário de perfil com validação |
| Anonimização, bloqueio ou eliminação | Existe rotina de hard delete ou anonimização? | Edge Function + SQL de deleção em cascata |
| Portabilidade | Usuário pode exportar dados em formato estruturado? | Download JSON/CSV dos dados pessoais |
| Informação sobre compartilhamento | Registro de quais terceiros recebem dados | Tabela `data_sharing_log` |
| Revogação de consentimento | Consentimentos são registrados e revogáveis? | Tabela `consents` com `revoked_at` |
| Oposição | Usuário pode se opor a tratamentos baseados em legítimo interesse? | Configurações de privacidade |
| Revisão de decisões automatizadas | Algoritmos afetam interesses do usuário? | Sistema de appeal/revisão humana |

**Princípios e guardrails técnicos:**

- **Minimização**: colete apenas dados estritamente necessários. Verifique tabelas por colunas como `cpf`, `rg`, `phone`, `address` que não são essenciais ao negócio
- **Consentimento**: deve ser livre, específico, informado e revogável. Evite consentimentos pré-marcados ou bundled (um único checkbox para várias finalidades)
- **Finalidade**: cada dado coletado deve ter finalidade clara documentada. Não reutilize dados para finalidades não informadas
- **Retenção**: implemente eliminação automática após o fim da finalidade:
  ```sql
  -- Exemplo: deletar logs antigos automaticamente
  DELETE FROM public.activity_logs WHERE created_at < NOW() - INTERVAL '90 days';
  ```
- **Notificação de incidentes**: prepare rotina para notificar ANPD e titulares em caso de vazamento (art. 46, §3º)
- **DPO (Encarregado)**: verifique se o app processa dados em larga escala ou sensíveis — se sim, indique a necessidade de nomear um DPO
- **DPIA/RIPD**: para tratamentos de alto risco (dados sensíveis, profiling, monitoramento massivo), documente uma avaliação de impacto à proteção de dados

**PII em serviços externos:**

- **Procure**: envio de e-mail, nome, CPF, user ID para analytics, ads, chat widgets, error trackers:
  ```bash
  grep -rn "gtag\|fbq\|amplitude\|mixpanel\|sentry\|hotjar\|intercom" \
    src/ app/ --include="*.ts" --include="*.tsx"
  ```
- **Regra**: nunca enviar PII para third-parties sem anonimização ou base legal. User IDs devem ser hashes, não UUIDs reais
- **Sentry**: configure `beforeSend` para remover PII:
  ```typescript
  Sentry.init({
    dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
    beforeSend(event) {
      if (event.user) {
        delete event.user.email
        delete event.user.ip_address
      }
      return event
    }
  })
  ```

**Deleção de conta (hard delete vs soft delete):**

- Soft delete (`deleted_at`) **não** atende ao direito de eliminação da LGPD se os dados ainda puderem ser reidentificados
- Implemente hard delete ou anonimização irreversível:
  ```sql
  CREATE OR REPLACE FUNCTION delete_user_data(p_user_id UUID)
  RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
  BEGIN
    DELETE FROM public.profiles WHERE user_id = p_user_id;
    DELETE FROM public.orders WHERE user_id = p_user_id;
    DELETE FROM public.user_uploads WHERE user_id = p_user_id;
    -- Deletar arquivos do Storage via Edge Function
    -- Deletar conta de auth via service_role em Edge Function separada
  END;
  $$;
  ```

- Para checklist completo e templates de política de privacidade, veja `references/audit-details.md` → seção "LGPD" e `references/infrastructure.md` → seção "LGPD/GDPR checklist"

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

#### 27d. PII detection & data classification — mapear e proteger dados pessoais
Não é possível proteger o que você não sabe que existe. Apps frequentemente acumulam dados pessoais sem catalogação, aumentando o risco de vazamento e multas regulatórias.

- **Mapear colunas com PII no banco**:
  ```sql
  -- Listar colunas suspeitas de conter PII
  SELECT table_name, column_name, data_type
  FROM information_schema.columns
  WHERE table_schema = 'public'
    AND column_name IN ('email', 'cpf', 'phone', 'phone_number', 'address', 'document', 'passport', 'rg', 'birth_date', 'name', 'full_name')
  ORDER BY table_name, column_name;
  ```
- **Classificação de dados**: categorize em `público`, `interno`, `confidencial`, `sensível` (LGPD art. 5º, II). Dados sensíveis (saúde, biometria, convicção religiosa, etc.) exigem medidas técnicas extras
- **Verificar**: esses dados são realmente necessários? Podem ser anonimizados ou pseudonimizados?
- **Marcar schemas/tabelas sensíveis**: documente no relatório quais tabelas contêm PII e quais controles existem
- Para padrões detalhados, veja `references/audit-details.md` → seção "PII detection"

#### 27e. Backup, disaster recovery & RTO/RPO
Segurança não é apenas prevenir ataques — é também garantir recuperação. A LGPD e boas práticas exigem que você consiga restaurar dados e continuar operando após incidentes.

- **Verificar**: o projeto tem backups automáticos configurados no Supabase Dashboard?
- **Verificar**: backups são testados periodicamente? (um backup que não restaura é inútil)
- **Definir RTO/RPO**:
  - RTO (Recovery Time Objective): tempo máximo aceitável de indisponibilidade
  - RPO (Recovery Point Objective): quantidade máxima de dados aceitável perder
- **Backup criptografado**: backups devem estar criptografados em repouso e em trânsito
- **Cópias fora do ambiente primário**: para dados críticos, considere backup em região/secundária ou exportação criptografada
- Para padrões detalhados, veja `references/audit-details.md` → seção "Backup e DR"

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

Para cada uma das 38 categorias auditadas, registre uma entrada:

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
| LGPD & Privacidade | [nota /10] | [nota /10] | |
| Supply Chain & Integridade | [nota /10] | [nota /10] | |
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

### Passo 4.5 — Red Team: usar Claude para atacar o próprio sistema

Após as verificações passarem, execute um passo final de adversarial testing. Use o seguinte prompt contra os arquivos do projeto para tentar encontrar brechas que a auditoria sistemática pode ter deixado passar:

```
"Analise o código deste projeto como um atacante tentaria explorar.
Procure por:
- Race conditions: há operações que deveriam ser atômicas mas não são?
- IDOR: é possível acessar recursos de outro usuário manipulando IDs?
- Validações faltando: algum input chega ao banco sem validação server-side?
- Lógica de negócio explorável: combinando ações legítimas, é possível ganhar
  algo indevido (saldo extra, acesso premium, bônus duplo)?
- Inputs sem limite de tamanho que poderiam causar DoS?
Seja criativo — pense em combinações não óbvias de fluxos legítimos."
```

Tudo que este passo encontrar deve ser corrigido antes de encerrar. Repita se necessário.

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
| `README.md` | Documentação pública do repositório GitHub — **deve ser atualizado** sempre que uma nova versão for criada |

## Regra de atualização do README.md

Sempre que esta skill for atualizada (nova versão, nova task, nova categoria), o `README.md` deve ser atualizado para refletir:
- Versão atual no topo
- Nova entrada no Changelog
- Novas linhas na tabela de cobertura (se houver novas tasks)

---

## Comando de atualização — baixar nova versão do GitHub

**Acionado por**: "atualiza a skill", "update security-auditor", "baixa nova versão da skill", "instala update da skill", "atualiza o auditor de segurança", "tem update da skill?", "quero a versão mais recente da skill"

Quando o usuário pedir atualização desta skill, **NÃO inicie uma auditoria**. Execute apenas:

```bash
cd ~/.claude/skills/security-auditor && git pull origin main
```

Após o pull:
1. Leia as primeiras linhas do `CHANGELOG.md` para ver o que mudou na versão mais recente
2. Informe o usuário:
   - A versão instalada anteriormente
   - A versão instalada agora
   - As principais novidades (resumo do CHANGELOG)
3. Se o pull falhar (sem rede, conflitos, etc.), informe o erro e sugira:
   ```bash
   # Re-instalação limpa (se git pull falhar)
   rm -rf ~/.claude/skills/security-auditor
   git clone https://github.com/Empire-Business/security-auditor ~/.claude/skills/security-auditor
   ```
