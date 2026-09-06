# Schemas

JSON Schema Draft 2020-12 no subconjunto explícito suportado pelo runtime. Campos desconhecidos são
rejeitados, não descartados. YAML de projeto/task é lido com parser seguro e validação de schema.
Condições entre campos/arquivos também são verificadas pelo runtime e não cabem somente no schema.

Schemas de risk-decision e release documentam registros opcionais de integração. Nenhum deles concede
permissão por conter uma string; esta release não transforma exceção em waiver automático ou publica
uma aplicação por validar um JSON. Referência externa confiável permanece necessária.
