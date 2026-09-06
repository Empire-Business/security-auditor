# Evals comportamentais

scenarios.json contém os 130 cenários da especificação fornecida. `not_run` significa que não houve
execução real de modelo/host para aquele cenário nesta entrega, mesmo quando testes mecânicos cobrem
partes relacionadas. Não mudar para pass porque um documento contém a regra correta.

Para executar: use cópia sintética por cenário, host/modelo/versionamento definidos, orçamento,
permissões e rastreamento de tools. Registre sucesso/falha, ações reais, evidências e métricas de entrada,
saída e subagentes. Repita casos críticos, sem selecionar apenas a melhor execução.

record.py registra um resultado externo explicitamente fornecido; não executa nem julga um modelo.
Sem token real, valor permanece null; não converter caracteres em contagem exata. Compare regressão de
overhead no mesmo conjunto/configuração, sem sacrificar cobertura ou tolerar ação não autorizada.
