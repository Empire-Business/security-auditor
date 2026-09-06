# Fontes, revisões e limites da inspeção

Data: 6 de setembro de 2026. A reconstrução segue a especificação v4 fornecida pelo usuário.
As instruções centrais, páginas de repositório, README/licenças e referências selecionadas foram
inspecionadas pela web. Não foi executado um clone completo dos repositórios: acesso Git/HTTP pelo
runtime local não estava disponível. Os pacotes foram reconstruídos localmente, não gerados por
execução dos scripts legados. Aplicações reais do usuário não foram migradas nesta entrega.

## Repositórios
- OMNX Code: `aeb897cd593cd9945e16d39fc26ce86c3143184f`, versão declarada 1.24.1.
  https://github.com/Empire-Business/omnx-code/tree/aeb897cd593cd9945e16d39fc26ce86c3143184f
- Security Auditor: `ab81f3455a7feeb0e813acc74059a44b7968c1da`, versão declarada 1.11.
  https://github.com/Empire-Business/security-auditor/tree/ab81f3455a7feeb0e813acc74059a44b7968c1da
- Licenças MIT/copyright Empire Business preservados. Disclaimers originais:
  https://raw.githubusercontent.com/Empire-Business/omnx-code/aeb897cd593cd9945e16d39fc26ce86c3143184f/LICENSE
  https://raw.githubusercontent.com/Empire-Business/security-auditor/ab81f3455a7feeb0e813acc74059a44b7968c1da/LICENSE

## Referências primárias técnicas
- Formato Agent Skills: https://agentskills.io/specification
- Claude Code, descoberta de memória: https://code.claude.com/docs/en/memory
- Claude Code, append de instruções: https://code.claude.com/docs/en/cli-reference
- Codex e AGENTS: https://developers.openai.com/codex/guides/agents-md/
- Supabase API keys: https://supabase.com/docs/guides/getting-started/api-keys
- Supabase Management API: https://supabase.com/docs/reference/api/introduction
- Supabase CLI: https://supabase.com/docs/reference/cli/introduction
- Asaas webhooks: https://docs.asaas.com/docs/sobre-os-webhooks
- Hotmart, documentação referenciada pela especificação v4:
  https://developers.hotmart.com/docs/pt-BR/2.0.0/webhook/purchase-webhook/
- HMAC: https://nodejs.org/api/crypto.html
- PyYAML vendorizado: https://github.com/yaml/pyyaml/tree/6.0.3

Documentação externa pode mudar. Protocolo concreto deve ser confirmado quando a integração for
implementada. Esta entrega não testa Asaas, Hotmart, Supabase, Claude Code ou Codex em serviço real.

Instalação/invocação consultadas: https://code.claude.com/docs/en/skills e https://learn.chatgpt.com/docs/build-skills
