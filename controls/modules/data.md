# Dados, exclusão e recuperação

Carregue este módulo somente quando a fronteira pertinente fizer parte do escopo. Resultados se limitam ao snapshot, evidência e ambiente.

## SEC-DATA-01 — Mudança destrutiva tem alvo e recuperação

**Aplica-se:** schema, exclusão ou transformação de dados.

**Verifique:** Identificar ambiente, autorização, backup verificável, compatibilidade e rollback/compensação. Não substituir db push por db reset --linked. CRUD normal não exige migration por ser DML.

**Evidência pertinente:** Fixture de atualização/restauração e compatibilidade quando versões coexistem; nunca reset real automático.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.

## SEC-DATA-02 — Minimizar e proteger dados pessoais

**Aplica-se:** coleta, export, retenção ou dados sensíveis.

**Verifique:** Classificar uso e acesso; limitar coleta, retenção, logs e destinos. Não declarar conformidade legal sem análise própria autorizada.

**Evidência pertinente:** Teste de acesso/export/exclusão pertinente e configuração observada sem dados reais.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.
