# Credenciais e segredos

Carregue este módulo somente quando a fronteira pertinente fizer parte do escopo. Resultados se limitam ao snapshot, evidência e ambiente.

## SEC-SECRET-01 — Impedir exposição de segredo privilegiado

**Aplica-se:** credenciais, logs, config, bundles ou prompts mudam.

**Verifique:** Distinguir chave pública de credencial privilegiada. Não ecoar valor no finding. Conferir fronteiras cliente/servidor, histórico e destinos externos.

**Evidência pertinente:** Referência localizada redigida, natureza da credencial e caminho de exposição demonstrado.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.

## SEC-SECRET-02 — Armazenar segundo capacidade criptográfica necessária

**Aplica-se:** armazenamento/verificação/uso de credenciais.

**Verifique:** Senha usa verificador apropriado; token próprio pode usar hash; HMAC precisa chave disponível ao cálculo; credencial de saída precisa armazenamento protegido recuperável. PAT Supabase Management API não substitui genericamente chave Data API.

**Evidência pertinente:** Inspeção da finalidade e teste do protocolo; revogação/rotação somente com autorização específica.

**Retorno:** pass/fail exigem evidência localizada; unknown quando falta capacidade; not_applicable exige justificativa. Não crie Task nem aplique patch durante a revisão.
