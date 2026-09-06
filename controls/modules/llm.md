# LLM, RAG e ferramentas

Carregue este módulo somente quando a fronteira pertinente fizer parte do escopo. Resultados se limitam ao snapshot, evidência e ambiente.

## SEC-LLM-01 — Separar conteúdo recuperado de autoridade

**Aplica-se:** agent, tool, prompt, issue, RAG ou saída de modelo.

**Verifique:** Instruções em dados não autorizam ferramentas. Verificar ações, argumentos, destinos e escopo com controles fora do texto sempre que possível.

**Evidência pertinente:** Fixture de prompt injection tentando exfiltrar segredo/alterar política; limite real de ferramentas declarado.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.

## SEC-LLM-02 — Preservar isolamento e custo de delegação

**Aplica-se:** RAG, memória, agentes ou contexto compartilhado.

**Verifique:** Verificar tenant na busca/cache/tools, redaction e limites de chamadas/profundidade. Não declarar subagente independente sem execução real.

**Evidência pertinente:** Teste cruzado de recuperação e cenário de recursão/estouro com saída parcial explícita.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.
