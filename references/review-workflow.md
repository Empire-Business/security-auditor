# Fluxo do especialista

1. Receber objetivo e limites, sem instalar framework no projeto.
2. Validar identidade, modo, snapshot e capacidades. Se falta integração, declarar self_review/limitação.
3. Mapear ator → entrada → confiança → efeito numa nota curta.
4. Selecionar controles aplicáveis, carregar só seus módulos e dependências necessárias.
5. Verificar código/configuração e testes autorizados; nunca produção por conveniência.
6. Retornar cobertura e evidências. Unknown é conclusão válida quando falta prova, mas não libera gate crítico.
7. Encerrar: OMNX coordena eventual correção. Não manter Tasks ou ativar orquestrador novamente.

Design examina proposta. Delta lê fronteira pertinente, inclusive helpers inalterados. Full usa descoberta
progressiva e declara o que não avaliou. Nenhum modo é autorização automática para pentest ativo.
Expansão dentro da mesma fronteira tem motivo e orçamento; independentes são observações separadas.
Auditorias sem findings são legítimas. Não gerar relatório ornamental para justificar custo.
