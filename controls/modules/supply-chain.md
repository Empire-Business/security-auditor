# Dependências e entrega

Carregue este módulo somente quando a fronteira pertinente fizer parte do escopo. Resultados se limitam ao snapshot, evidência e ambiente.

## SEC-SUPPLY-01 — Verificar origem e integridade de artefatos

**Aplica-se:** instalação, update, dependência, build ou workflow.

**Verifique:** Fixar fonte, validar checksum confiado externamente, assinatura quando real. Não executar pacote para decidir se é confiável. Não curl|sh/npx@latest oculto.

**Evidência pertinente:** Digest/fonte verificados antes de execução; teste de alteração e preservação do instalado.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.

## SEC-SUPPLY-02 — Scripts e CI não ampliam autoridade

**Aplica-se:** test, postinstall, hooks, workflows ou política.

**Verifique:** Inspecionar comandos e execução em sandbox sem credenciais de produção. Política da própria mudança não pode aprovar a si mesma. Advisory requer fonte atual e avaliação de alcance.

**Evidência pertinente:** Teste/inspeção de permissões e referência confiável da política, não só YAML no PR.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.
