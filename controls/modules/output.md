# Saídas, navegador e exposição

Carregue este módulo somente quando a fronteira pertinente fizer parte do escopo. Resultados se limitam ao snapshot, evidência e ambiente.

## SEC-OUTPUT-01 — Renderizar e serializar sem exposição indevida

**Aplica-se:** HTML, templates, API responses ou download.

**Verifique:** Verificar encoding por contexto, sanitização quando HTML intencional e minimização de campos retornados. Não confiar em conteúdo de integração/RAG.

**Evidência pertinente:** Teste de conteúdo não confiável no contexto real e negativa de campo sensível.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.

## SEC-OUTPUT-02 — Logs e diagnósticos não vazam dados

**Aplica-se:** logging, erros, tickets ou observabilidade.

**Verifique:** Redigir antes de persistir/transmitir. Respeitar retenção e acesso; recusa/falha de screenshot não deve impedir ticket nem criar loop.

**Evidência pertinente:** Captura controlada de saída confirma ausência de segredo e falha do próprio diagnóstico é contida.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.

## SEC-OUTPUT-03 — Políticas do navegador protegem o fluxo sem quebrá-lo

**Aplica-se:** cookies, CORS, CSP, CSRF, framing ou cabeçalhos.

**Verifique:** Escolher políticas por origem, sessão e ameaças. CORS não substitui auth. COOP/COEP não são obrigação universal. Testar fluxos legítimos afetados.

**Evidência pertinente:** Inspeção de configuração efetiva mais teste de origem/sessão adversa e fluxo permitido.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.
