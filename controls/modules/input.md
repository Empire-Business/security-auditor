# Entrada e interpretação

Carregue este módulo somente quando a fronteira pertinente fizer parte do escopo. Resultados se limitam ao snapshot, evidência e ambiente.

## SEC-INPUT-01 — Impedir injeção na linguagem de destino

**Aplica-se:** input alcança SQL, shell, template, regex ou interpretador.

**Verifique:** Seguir origem até sink; parâmetros de consulta, argumentos de processo sem shell e allowlists estruturais quando necessárias. Escaping genérico não cobre todos os interpretadores.

**Evidência pertinente:** Teste malicioso controlado e inspeção de parametrização no sink real.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.

## SEC-INPUT-02 — Limitar parsing e consumo

**Aplica-se:** parser, payload, filtros, serialização ou endpoints.

**Verifique:** Validar tipos, tamanho, profundidade, duplicatas relevantes e limites de trabalho. Não impor regex arbitrária incompatível com dados legítimos.

**Evidência pertinente:** Casos limite, payload grande, tipo inválido e tempo/erro delimitado; sem execução de tags YAML.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.
