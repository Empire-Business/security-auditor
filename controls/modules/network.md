# Rede e destinos

Carregue este módulo somente quando a fronteira pertinente fizer parte do escopo. Resultados se limitam ao snapshot, evidência e ambiente.

## SEC-NET-01 — Evitar SSRF e redirecionamento indevido

**Aplica-se:** backend obtém URL ou faz chamada controlada por input.

**Verifique:** Restringir destinos, esquema, redirects, resolução e endereços internos conforme modelo. Conferir revalidação após redirecionamento e credenciais transmitidas.

**Evidência pertinente:** Teste em servidor local isolado de destino proibido/redirecionado, sem sondar infraestrutura real.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.

## SEC-NET-02 — Delimitar retries, timeout e efeitos externos

**Aplica-se:** integração, API ou operação remota.

**Verifique:** Timeout não prova falha do efeito. Verificar identidade/idempotência antes de repetir; limitar retries e credenciais ao destinatário.

**Evidência pertinente:** Teste de resposta perdida e retry sem duplicar efeito; timeout/circuito proporcional.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.
