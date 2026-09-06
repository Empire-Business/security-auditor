# Eventos externos

Carregue este módulo somente quando a fronteira pertinente fizer parte do escopo. Resultados se limitam ao snapshot, evidência e ambiente.

## SEC-WEBHOOK-01 — Autenticar conforme protocolo do provedor

**Aplica-se:** entrada de evento externo.

**Verifique:** Consultar protocolo/versão oficial. Asaas e Hotmart possuem mecanismos de header documentados; não inventar HMAC. Autenticar antes de persistência privilegiada ou efeitos.

**Evidência pertinente:** Teste de credencial ausente, inválida e válida no endpoint real; limites de corpo e acesso relevantes.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.

## SEC-WEBHOOK-02 — Idempotência precede efeitos e resiste a concorrência

**Aplica-se:** evento pode repetir ou produzir efeito financeiro/acesso.

**Verifique:** Verificar identidade no escopo provedor+conta/integração+evento. Recebido não equivale a processado. Inspecionar transação/estado/outbox conforme necessário, sem exigir fila universal.

**Evidência pertinente:** Teste concorrente de duplicata, falha entre persistência e efeito e recuperação sem perda/duplicação.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.

## SEC-WEBHOOK-03 — Ordenar estados e reconciliar reentregas

**Aplica-se:** cancelamento, estorno, renovação ou evento fora de ordem.

**Verifique:** Seguir transições aprovadas do PRD e política da fonte. Nunca último webhook vence indiscriminadamente. Não prometer exactly-once na rede.

**Evidência pertinente:** Teste de ordem invertida, replay, conta distinta com mesmo ID e reconciliação.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.
