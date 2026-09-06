# Contrato 2.0

Schemas em contracts/. A versão do protocolo não é a versão de release da skill.
Request identifica projeto, Task/orquestrador ou null standalone, modo design/delta/full, objetivo,
snapshot real, controles, superfícies, permissões e orçamento. Permissão no JSON é limite solicitado,
não concessão do host. Sem apps writes, sem produção implícita e sem rede default.

Response repete request/projeto/Task/modo/policy/registry/snapshot. Cada controle solicitado aparece
exatamente uma vez; adicionados têm origin added e relação justificada. Não omitir não suportado.
Execução completed pode ter resultado unknown avaliado; cobertura adiada ou descoberta incompleta é partial.
Pass/fail exige evidência pertinente; not_applicable explica por que condição não existe.

Finding: ID, controle, evidências, severidade, confiança, ator/condição, consequência, recomendação e exposição.
Não tem status de execução. Observação independente não vira autorização para audit full/correção.
Evidência: ID, tipo, referência, resultado, ambiente, instante, resumo e path/hash quando pertinente.
Não usar fixture ilustrativa como evidência operacional. Métrica não disponível = null.

Helper response-template gera apenas unknown/deferred e partial. O agente executa a revisão e preenche
honestamente. validate-response verifica consistência, não descobre vulnerabilidade nem autentica revisor.
Resultados inválidos não podem ser simplificados para palavra PASS; uma tentativa de reparo, depois limitação.

Este release usa política local distribuída, sem overrides ad hoc. Política corporativa diferente pede
adaptador revisado com origem confiável, não edição do patch para remover bloqueio.
