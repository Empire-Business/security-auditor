# RLS Avançado — Multi-tenant, Performance, Testing e RBAC

## Índice
- [Padrões multi-tenant](#multi-tenant)
- [Performance: (SELECT auth.uid())](#performance)
- [Índices obrigatórios](#indices)
- [Event trigger para auto-habilitar RLS](#event-trigger)
- [Comportamentos silenciosos do RLS](#silent-failures)
- [RBAC via Custom Access Token Hooks](#rbac)
- [app_metadata vs user_metadata](#metadata)
- [Testando políticas com pgTap](#pgtap)

---

## Padrões multi-tenant {#multi-tenant}

### Padrão 1 — Isolamento por user_id (mais simples)

Para apps onde cada usuário tem seus próprios dados:

```sql
ALTER TABLE public.documentos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "SELECT proprios" ON public.documentos FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "INSERT proprios" ON public.documentos FOR INSERT TO authenticated
  WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "UPDATE proprios" ON public.documentos FOR UPDATE TO authenticated
  USING ((SELECT auth.uid()) = user_id)
  WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "DELETE proprios" ON public.documentos FOR DELETE TO authenticated
  USING ((SELECT auth.uid()) = user_id);
```

### Padrão 2 — Isolamento por tenant_id via JWT (recomendado para performance)

Injete o `tenant_id` no JWT via Custom Access Token Hook e leia diretamente do token — sem join:

```sql
-- Função helper para extrair tenant_id do JWT
CREATE OR REPLACE FUNCTION public.get_tenant_id()
RETURNS uuid
LANGUAGE sql STABLE
AS $$
  SELECT (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid;
$$;

-- Política de isolamento por tenant
CREATE POLICY "Isolamento por tenant"
  ON public.pedidos FOR ALL TO authenticated
  USING (tenant_id = (SELECT public.get_tenant_id()))
  WITH CHECK (tenant_id = (SELECT public.get_tenant_id()));
```

### Padrão 3 — Acesso por equipe/organização com tabela de membros

Para apps onde múltiplos usuários compartilham dados de uma conta/organização:

```sql
-- Função SECURITY DEFINER para verificar membership (evita recursão RLS)
CREATE OR REPLACE FUNCTION public.has_role_on_account(
  account_id uuid,
  account_role varchar(50) DEFAULT NULL
) RETURNS boolean
LANGUAGE sql SECURITY DEFINER SET search_path = ''
AS $$
  SELECT EXISTS(
    SELECT 1 FROM public.membros
    WHERE membros.user_id = (SELECT auth.uid())
      AND membros.account_id = has_role_on_account.account_id
      AND (membros.role = has_role_on_account.account_role
           OR has_role_on_account.account_role IS NULL)
  );
$$;

-- Política: membros leem dados da conta
CREATE POLICY "Membros leem conta"
  ON public.contas FOR SELECT TO authenticated
  USING (public.has_role_on_account(id));

-- Política: apenas admins podem deletar
CREATE POLICY "Admins deletam conta"
  ON public.contas FOR DELETE TO authenticated
  USING (public.has_role_on_account(id, 'admin'));
```

**Por que usar SECURITY DEFINER aqui?**
Se a tabela `membros` também tem RLS, a função de verificação de membership causaria recursão. Com `SECURITY DEFINER`, ela roda como o owner da função (postgres) e não enfrenta RLS.

---

## Performance: (SELECT auth.uid()) {#performance}

Esta é uma das otimizações mais impactantes de RLS. A diferença é enorme em tabelas com muitas linhas.

```sql
-- ❌ LENTO: auth.uid() é avaliado para cada linha da tabela
CREATE POLICY "lento" ON public.tabela FOR SELECT TO authenticated
  USING (auth.uid() = user_id);

-- ✅ RÁPIDO: (SELECT auth.uid()) é avaliado uma vez via initPlan e cacheado
CREATE POLICY "rapido" ON public.tabela FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = user_id);
```

O wrapper `(SELECT ...)` faz o PostgreSQL tratar a expressão como um subquery de initPlan — ela é avaliada uma vez por query, não uma vez por linha. O impacto é de até **1000x** em tabelas grandes.

Para auditar todas as políticas que usam `auth.uid()` sem o wrapper:

```sql
SELECT schemaname, tablename, policyname, qual
FROM pg_policies
WHERE schemaname = 'public'
  AND qual LIKE '%auth.uid()%'
  AND qual NOT LIKE '%(SELECT auth.uid())%';
```

---

## Índices obrigatórios {#indices}

Toda coluna usada em cláusula USING ou WITH CHECK de uma política RLS deve ter índice:

```sql
-- Verificar colunas sem índice usadas em policies
SELECT DISTINCT p.tablename, p.qual
FROM pg_policies p
WHERE p.schemaname = 'public'
  AND (p.qual LIKE '%user_id%' OR p.qual LIKE '%tenant_id%' OR p.qual LIKE '%account_id%');

-- Criar índices necessários
CREATE INDEX IF NOT EXISTS ix_tabela_user_id ON public.tabela USING btree (user_id);
CREATE INDEX IF NOT EXISTS ix_tabela_tenant_id ON public.tabela USING btree (tenant_id);
```

Sem índice, cada SELECT faz full table scan filtrado por RLS — catastrófico em produção.

---

## Event trigger para auto-habilitar RLS {#event-trigger}

Crie um event trigger para garantir que qualquer nova tabela no schema `public` já nasce com RLS habilitado:

```sql
CREATE OR REPLACE FUNCTION rls_auto_enable()
RETURNS EVENT_TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
DECLARE
  cmd record;
BEGIN
  FOR cmd IN
    SELECT * FROM pg_event_trigger_ddl_commands()
    WHERE command_tag IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO')
    AND object_type IN ('table', 'partitioned table')
  LOOP
    IF cmd.schema_name = 'public' THEN
      EXECUTE format(
        'ALTER TABLE IF EXISTS %s ENABLE ROW LEVEL SECURITY',
        cmd.object_identity
      );
    END IF;
  END LOOP;
END;
$$;

CREATE EVENT TRIGGER ensure_rls
  ON ddl_command_end
  WHEN TAG IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO')
  EXECUTE FUNCTION rls_auto_enable();
```

**Para verificar se o trigger já existe:**
```sql
SELECT evtname, evtevent, evtenabled
FROM pg_event_trigger
WHERE evtname = 'ensure_rls';
```

---

## Comportamentos silenciosos do RLS {#silent-failures}

Este é o comportamento mais confuso do RLS para desenvolvedores iniciantes. Diferente de erros de autenticação, violações de RLS **não retornam erros**:

| Operação | Comportamento quando RLS bloqueia | Impacto no código |
|----------|-----------------------------------|-------------------|
| SELECT   | Retorna 0 linhas (sem erro)       | Parece que o dado não existe |
| UPDATE   | Afeta 0 linhas (sem erro)         | `count` retorna 0, nenhum dado modificado |
| DELETE   | Afeta 0 linhas (sem erro)         | `count` retorna 0, nenhum dado deletado |
| INSERT   | Lança erro HTTP 403               | Único que gera erro visível |

**Implicação para auditoria:** Se um `.update()` retorna `{ count: 0 }` e o dado existe, provavelmente é RLS bloqueando — não um bug na query.

**RLS habilitado sem políticas = deny-all:**
```sql
-- Isso habilita RLS mas bloqueia TODOS os acessos (nenhuma política = nada passa)
ALTER TABLE public.tabela ENABLE ROW LEVEL SECURITY;
-- Se esquecer de criar as políticas, queries retornam vazio silenciosamente
```

---

## RBAC via Custom Access Token Hooks {#rbac}

O padrão mais seguro e performático para Role-Based Access Control:

```sql
-- 1. Criar tipos
CREATE TYPE public.app_role AS ENUM ('admin', 'moderator', 'member');
CREATE TYPE public.app_permission AS ENUM ('canais.deletar', 'mensagens.deletar', 'usuarios.banir');

-- 2. Tabelas de roles e permissões
CREATE TABLE public.user_roles (
  id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  user_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
  role app_role NOT NULL,
  UNIQUE (user_id, role)
);

CREATE TABLE public.role_permissions (
  id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  role app_role NOT NULL,
  permission app_permission NOT NULL,
  UNIQUE (role, permission)
);

-- 3. Hook que injeta o role no JWT
CREATE OR REPLACE FUNCTION public.custom_access_token_hook(event jsonb)
RETURNS jsonb LANGUAGE plpgsql STABLE AS $$
DECLARE
  claims jsonb;
  user_role public.app_role;
BEGIN
  SELECT role INTO user_role FROM public.user_roles
  WHERE user_id = (event->>'user_id')::uuid;

  claims := event->'claims';
  claims := jsonb_set(claims, '{user_role}',
    to_jsonb(COALESCE(user_role, 'member'::app_role)));
  event := jsonb_set(event, '{claims}', claims);
  RETURN event;
END;
$$;

-- 4. Função de autorização usada nas políticas RLS
CREATE OR REPLACE FUNCTION public.authorize(requested_permission app_permission)
RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = '' AS $$
DECLARE
  user_role public.app_role;
BEGIN
  SELECT (auth.jwt() ->> 'user_role')::public.app_role INTO user_role;
  RETURN EXISTS(
    SELECT 1 FROM public.role_permissions
    WHERE permission = requested_permission AND role = user_role
  );
END;
$$;

-- 5. Usar em política RLS
CREATE POLICY "Admins deletam canais"
  ON public.canais FOR DELETE TO authenticated
  USING ((SELECT public.authorize('canais.deletar')));
```

**Habilitar no Dashboard:** Authentication → Hooks → Custom Access Token → selecionar `public.custom_access_token_hook`

**Verificar role no TypeScript:**
```typescript
const { data: { user } } = await supabase.auth.getUser()
const role = (user?.app_metadata?.user_role as string) ?? 'member'
if (role !== 'admin') {
  return NextResponse.json({ error: 'Acesso negado' }, { status: 403 })
}
```

---

## app_metadata vs user_metadata {#metadata}

Esta distinção é crítica para segurança:

| Metadata      | Quem pode alterar                     | Uso correto                    |
|---------------|---------------------------------------|--------------------------------|
| `user_metadata` | O próprio usuário (`updateUser()`)  | Preferências, nome, avatar     |
| `app_metadata`  | Apenas service_role (servidor)      | Roles, permissões, tenant_id   |

**Vulnerabilidade se usar user_metadata para autorização:**
```sql
-- ❌ PERIGOSO: usuário pode se promover a admin mudando user_metadata
USING (auth.jwt()->'user_metadata'->>'role' = 'admin')

-- ✅ SEGURO: apenas service_role pode alterar app_metadata
USING (auth.jwt()->'app_metadata'->>'role' = 'admin')
```

Para detectar policies usando `user_metadata` para autorização:
```sql
SELECT tablename, policyname, qual
FROM pg_policies
WHERE schemaname = 'public'
  AND qual LIKE '%user_metadata%';
```

---

## Testando políticas com pgTap {#pgtap}

Use `basejump-supabase_test_helpers` para testar RLS de forma automatizada:

```sql
BEGIN;
CREATE EXTENSION IF NOT EXISTS "basejump-supabase_test_helpers" VERSION '0.0.6';
SELECT no_plan();

-- Criar usuários de teste
SELECT tests.create_supabase_user('dono', 'dono@test.com');
SELECT tests.create_supabase_user('intruso', 'intruso@test.com');

-- Inserir dado (bypass RLS com service_role)
SET LOCAL ROLE service_role;
INSERT INTO public.documentos (user_id, titulo)
VALUES (tests.get_supabase_uid('dono'), 'Dado Secreto');

-- Teste: dono vê seu dado
SELECT tests.authenticate_as('dono');
SELECT isnt_empty(
  $$ SELECT * FROM public.documentos WHERE titulo = 'Dado Secreto' $$,
  'Dono deve ver seu documento'
);

-- Teste: intruso não vê dado alheio
SELECT tests.authenticate_as('intruso');
SELECT is_empty(
  $$ SELECT * FROM public.documentos WHERE titulo = 'Dado Secreto' $$,
  'Intruso não deve ver documento alheio'
);

-- Teste: intruso não consegue deletar dado alheio
SELECT results_eq(
  $$ DELETE FROM public.documentos WHERE titulo = 'Dado Secreto' RETURNING id $$,
  ARRAY[]::uuid[],
  'Intruso não deve deletar documento alheio'
);

SELECT * FROM finish();
ROLLBACK;
```

Execute com: `supabase test db`

Para auditar se existem testes de RLS no projeto:
```bash
# Procurar arquivos de teste SQL com RLS
find . -name "*.sql" -path "*/tests/*" | head -20
ls supabase/tests/ 2>/dev/null || echo "Sem testes de banco de dados"
```
