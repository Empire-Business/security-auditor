# Dinheiro e direitos de acesso

Carregue este módulo somente quando a fronteira pertinente fizer parte do escopo. Resultados se limitam ao snapshot, evidência e ambiente.

## SEC-PAY-01 — Validar valores e destinatários com fonte confiável

**Aplica-se:** checkout, preço, pagamento ou acesso pago.

**Verifique:** Não confiar em preço/moeda/beneficiário vindo do cliente. Verificar precisão numérica e vínculo da compra ao produto/conta corretos.

**Evidência pertinente:** Teste de valor/moeda/produto adulterados e caso legítimo com representação monetária adequada.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.

## SEC-PAY-02 — Preservar consistência de estados e acesso

**Aplica-se:** assinatura, renovação, reembolso, chargeback ou suspensão.

**Verifique:** Aplicar contrato funcional, não inventar regra de produto. Acesso, matrícula, compra e evento não são a mesma entidade. Teste não pode cobrar dinheiro real sem autorização.

**Evidência pertinente:** Cenários de cancelamento/estorno/renovação e falha parcial em sandbox, com resultado de acesso esperado.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.
