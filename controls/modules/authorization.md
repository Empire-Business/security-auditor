# Autorização

Carregue este módulo somente quando a fronteira pertinente fizer parte do escopo. Resultados se limitam ao snapshot, evidência e ambiente.

## SEC-AUTHZ-01 — Autorizar ação e recurso no servidor

**Aplica-se:** leitura, escrita, função ou efeito protegido.

**Verifique:** Seguir identidade até decisão de autorização. UI desabilitada não protege API. Verificar objeto, organização, ação, papel e privilégio administrativo.

**Evidência pertinente:** Teste positivo e negativo de acesso direto, sem depender da tela.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.

## SEC-AUTHZ-02 — Privilégios e revogação respeitam limites

**Aplica-se:** admin, impersonação, convite, roles ou operações de suporte.

**Verifique:** Verificar caminhos privilegiados, origem de grants, alterações de papel e efeitos de revogação. Um backend com chave elevada continua precisando autorizar o ator.

**Evidência pertinente:** Teste de ator comum tentando ação privilegiada e caso administrativo legítimo.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.
