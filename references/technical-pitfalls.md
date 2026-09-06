# Armadilhas a verificar quando pertinentes

Supabase: separar Data API keys de PAT Management API. Não substituir service_role por PAT genericamente;
avaliar componente/privilégio/exposição. Chave publicável não é segredo; backend privilegiado ainda autoriza ator.
Claims: produtor e consumidor devem usar o mesmo namespace e origem protegida; testar fluxo real.
Webhooks: autenticar protocolo documentado para evento/versão. Asaas documenta header asaas-access-token;
Hotmart documenta X-HOTMART-HOTTOK nos fluxos pertinentes. Token não é assinatura HMAC do corpo.
Idempotência escopa conta/provedor/evento; considerar simultaneidade, ordem e falha parcial. Não exactly-once universal.
HMAC exige chave para cálculo; hash irreversível não substitui uso criptográfico. Credencial de saída é recuperável
pelo componente autorizado; senha de usuário normalmente não. Origem/rotação dependem do provedor.
Migração: nunca fallback automático para supabase db reset --linked. Comando indisponível não autoriza destruição.
Financeiro: preço/moeda/conta confiáveis, precisão apropriada, estados de negócio aprovados. Não teste cobrança real.
Privacidade: técnica não certifica legislação. Consultar fonte oficial/autoridade apropriada se conformidade for escopo.
Cabeçalhos, CAPTCHA, fila, SECURITY DEFINER e policies não são receitas universais; testar efeitos legítimos.

Fontes e revisões: reports/SOURCES.md. Confirmar documentação atual no momento de código específico.
