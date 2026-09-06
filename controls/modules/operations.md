# Operação, ambiente e evidências

Carregue este módulo somente quando a fronteira pertinente fizer parte do escopo. Resultados se limitam ao snapshot, evidência e ambiente.

## SEC-OPS-01 — Vincular evidência ao conteúdo e ambiente

**Aplica-se:** gate, release ou reuso de auditoria.

**Verifique:** HEAD sozinho não cobre working tree. Hash não prova autoria nem drift externo. Diferenciar design/static/test e não inventar produção verificada.

**Evidência pertinente:** Comparação de manifesto de arquivos/deps, policy/registry e ambiente relevante; recibo velho é rejeitado.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.

## SEC-OPS-02 — Respeitar autorização e estado de publicação

**Aplica-se:** deploy, push com hook, rotação ou efeito O2/O3.

**Verifique:** Done não é deployed. Identificar destino e autoridade. Falha de smoke test impede alegar release saudável; rollback de código não restaura efeito externo.

**Evidência pertinente:** Registro de autorização e resultado observado; teste de falha e recuperação em ambiente isolado.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.
