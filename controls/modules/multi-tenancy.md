# Isolamento entre tenants

Carregue este módulo somente quando a fronteira pertinente fizer parte do escopo. Resultados se limitam ao snapshot, evidência e ambiente.

## SEC-TENANT-01 — Isolar recursos na fronteira real de dados

**Aplica-se:** recursos pertencem a organizações ou usuários distintos.

**Verifique:** Validar associação ao tenant escolhido, filtro/policy/grants e acesso por ID direto. Não presumir um único tenant por usuário. Não substituir policies públicas legítimas cegamente.

**Evidência pertinente:** Usuários comuns A/B: acesso permitido próprio e negado cruzado, incluindo operação afetada.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.

## SEC-TENANT-02 — Transportar escopo em cache, storage e jobs

**Aplica-se:** cache, arquivos, URL assinada, export, busca ou execução assíncrona.

**Verifique:** Seguir tenant no nome de cache, chave de objeto, payload de job, lookup e download. RLS em uma tabela não cobre efeitos fora dela.

**Evidência pertinente:** Teste cruzado no caminho afetado de cache/storage/job; inspeção da origem de contexto.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.
