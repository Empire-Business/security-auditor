# Arquivos e extração

Carregue este módulo somente quando a fronteira pertinente fizer parte do escopo. Resultados se limitam ao snapshot, evidência e ambiente.

## SEC-FILE-01 — Conter paths, uploads e arquivos compactados

**Aplica-se:** upload, download, extração ou escrita em filesystem.

**Verifique:** Rejeitar traversal, links/special files, colisões, extensões perigosas e tamanho/razão abusivos conforme caso. Não confiar no nome MIME fornecido.

**Evidência pertinente:** Fixtures de ../, absoluto, symlink/hardlink, duplicatas e expansão excessiva; nenhum efeito fora da raiz.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.

## SEC-FILE-02 — Autorizar acesso ao conteúdo armazenado

**Aplica-se:** download, URL assinada ou publicação de arquivo.

**Verifique:** Validar recurso e ator antes de gerar URL/acesso. Limitar validade e exposição conforme objetivo. Caminho imprevisível não é autorização.

**Evidência pertinente:** Tentativa por outro usuário/tenant e link expirado no mecanismo real.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.
