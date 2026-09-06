# Identidade, sessão e recuperação

Carregue este módulo somente quando a fronteira pertinente fizer parte do escopo. Resultados se limitam ao snapshot, evidência e ambiente.

## SEC-AUTHN-01 — Validar identidade e sessão no caminho real

**Aplica-se:** login, sessão, tokens ou validação de identidade mudam.

**Verifique:** Inspecionar emissor/audience/expiração e origem da sessão; testar identidade válida, inválida e expirada. Não aceitar dados do frontend como identidade.

**Evidência pertinente:** Teste do fluxo real com token inválido/expirado e caso permitido; configuração compatível com o provedor.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.

## SEC-AUTHN-02 — Revogação e recuperação não ampliam privilégio

**Aplica-se:** logout, recuperação, MFA, convite ou troca de credencial.

**Verifique:** Verificar uso único, prazo, vínculo ao usuário, sessão após troca e risco de enumeração. MFA é exigência contextual, não função imposta a todo produto.

**Evidência pertinente:** Teste de reuso, expiração, identidade errada e revogação no mecanismo efetivo.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.

## SEC-AUTHN-03 — Claims têm origem e consumo coerentes

**Aplica-se:** claims personalizados ou autorização derivada de token.

**Verifique:** Comparar produtor/consumidor, namespace, origem editável e atualização de permissões. Não aprovar SQL por aparência.

**Evidência pertinente:** Fixture autenticar → obter claim → acessar → negar; credencial normal, não só administrativa.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.
