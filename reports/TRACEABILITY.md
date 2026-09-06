# Rastreabilidade e limites por invariante — v4

Os testes listados foram executados em fixtures locais. Um teste parcial de um invariante NÃO significa homologação de todo comportamento descrito. Os 130 cenários de agente em `evals/scenarios.json` continuam `not_run`.

| Invariante | Implementação/objetivo | Evidência determinística (sufixo do ID) | Limite de cobertura |
|---|---|---|---|
| INV-01 | Entrada AGENTS única | test_legacy_consolidated_preserves_app; test_fake_claude_argv_plan_preserves_default | Bootstrap planejado/testado com argv; hosts reais não executados. |
| INV-02 | Fontes canônicas | test_archive_resolves_id; test_checkpoint_detects_cancel | Semântica documental depende de avaliação do agente. |
| INV-03 | Task não concede autorização | test_proposed_not_ready; test_proposed_task_does_not_gain_execution_from_audit | Origem registrada é referência; identidade humana é validada no host, não pelo texto do CLI. |
| INV-04 | Roadmap e checkpoint sem backlog | test_terminal_task_needs_no_checkpoint; test_checkpoint_detects_cancel | Extração semântica é responsabilidade do agente/revisor e não foi medida por LLM. |
| INV-05 | Contrato de produto separado do código | test_protected_product_write | Regra documental implementada; julgamento código/PRD exige eval comportamental. |
| INV-06 | Done não significa deployed | test_done_not_deploy; test_no_automatic_production | CLI não executa deploy. |
| INV-07 | Mockups históricos | test_route_s0_no_auditor | Roteamento cobre bypass básico; decisão de UX e ausência de burocracia precisam de eval de agente. |
| INV-08 | UX/S/O independentes | test_route_s0_no_auditor; test_local_commit_not_universal_gate | CLI aplica classes fornecidas; não classifica semanticamente o diff por palavra-chave. |
| INV-09 | Auditoria delimitada com dependências | test_missing_control; test_no_empty_full_audit_gate_pass | Seleção real de superfície é análise do especialista. |
| INV-10 | Unknown e fail distintos | test_completed_unknown_not_gate_pass; test_missing_evidence_for_pass | Validator valida estrutura/relações; não prova a honestidade do emissor. |
| INV-11 | Evidência vinculada ao conteúdo | test_dirty_file_invalidates; test_git_index_change_invalidates; test_different_snapshot | Ambiente externo requer observação autorizada; não é consultado automaticamente. |
| INV-12 | Auditor não gerencia execução | test_permissions_do_not_allow_write; test_receipt_idempotency | Entrypoint do auditor é restrito; biblioteca Python compartilhada não é sandbox de sistema. |
| INV-13 | Aprovações escopadas | test_authorization_change_requires_origin; test_no_automatic_production | Não há serviço de autenticação de aprovadores neste kit. |
| INV-14 | Conteúdo não confiável não é ordem | test_yaml_executable_tag; test_scan_redacts_before_output; test_host_bootstrap_needs_trust | Resistência a prompt injection exige eval no modelo/host e isolamento real. |
| INV-15 | Preservar significado além de backup | test_instruction_cannot_disappear_into_backup; test_missing_block_mapping_blocks_plan | Engine verifica cobertura/mapeamento; não infere equivalência semântica infalível. |
| INV-16 | Migração recuperável e idempotente | test_second_apply_noop; test_rollback_interruption_resume; test_abrupt_subprocess_exit_releases_lock_and_resumes | Atomicidade por arquivo e journal; não transação atômica de filesystem inteiro. |
| INV-17 | Atualização de método não é mudança do produto | test_protected_product_write; test_install_preserves_modified_destination; test_future_schema_preserved | Instalação sempre em pasta nova; ativação no host é explícita. |
| INV-18 | Sem efeitos fora do escopo | test_no_automatic_production; test_protected_product_write | Julgamento de expansão de escopo depende também do agente. |
| INV-19 | Concorrência com CAS e locks | test_cas_task; test_lock_contention; test_owner_transfer_requires_origin | Lock local entre cooperadores; não exclusão distribuída nem defesa contra processo hostil no mesmo usuário. |
| INV-20 | Falha não vira sucesso fictício | test_false_completion; test_template_not_pass; test_unknown_enum | Execução real de agentes, browser e provedores não homologada. |
| INV-21 | Criar somente artefatos úteis | test_init_plan_no_mutation; test_doctor_read_only_even_without_setup | Não há auditoria/PRD/mockup criado no init; aderência conversacional depende do agente. |
| INV-22 | Orçamento e ciclos delimitados | test_size_limit; test_no_empty_full_audit_gate_pass | Limites de arquivo implementados; tokens reais e iterações do modelo não medidos. |
| INV-23 | Política não se autoenfraquece | test_policy_modified_rejected; test_registry_modified_rejected | Política local de pacote confiado; não enforcement independente de CI/branch protection. |
| INV-24 | Bloquear somente a operação afetada | test_local_commit_not_universal_gate; test_completed_unknown_not_gate_pass | Fallback/incidente está nas referências; incidentes reais não executados. |

IDs completos e resultados estão em `test-results.json` do pacote OMNX. O pacote auditor executa um subconjunto próprio independente; os testes OMNX não devem ser atribuídos ao auditor como execuções exclusivas.
