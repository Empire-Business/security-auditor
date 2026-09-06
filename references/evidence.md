# Evidências e cobertura

Snapshot lista arquivos explicitamente escolhidos com hashes e blobs do índice Git pertinente.
Inclua middleware, policies, lockfiles e configuração que sustentam a conclusão. Arquivo novo/dirty
é conteúdo real, não o HEAD anterior. Conteúdo secreto usa referência opaca, não hash público de valor.

Tipos não se confundem: static inspeciona código; test registra execução; configuration observa ambiente;
design analisa proposta; external_reference embasa protocolo. Nenhum demonstra automaticamente os demais.
Identidade comum negada importa em authz/tenant; cliente privilegiado não comprova isolamento.
Concorrência precisa de cenário concorrente quando risco é race. Scanner de strings apenas localiza candidatos.

Reuso só quando dependências e condições continuam compatíveis. HEAD igual, TTL recente ou mtime renovado
não bastam. Nova configuração/secret version/advisory pode invalidar conclusão sem diff no endpoint.
Este runtime revalida hashes dos arquivos listados. Verificação de drift remoto e origem independente exige
integração externa real, não preenchimento otimista de environment_observed.

Recibos pequenos S2/S3 podem ser persistidos pela OMNX no canal autorizado; sem findings ainda comprovam
cobertura. Histórico imutável; reteste cria novo AUD-id. Não reescrever achado como se nunca existisse.
Hash não é assinatura; review_kind é declaração verificável pelo contexto, não atestação automática.
Se exigir CI assinado, implementar e validar integração própria antes de anunciar enforcement.

Redigir antes de saída. Não copiar token, senha, payload pessoal ou PoC sensível para versão pública.
Ao exceder limite, preservar resultado autorizado e cobertura parcial; nunca truncar silenciosamente finding.
