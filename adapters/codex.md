# Codex

Codex possui descoberta própria de AGENTS.md. Respeite hierarquia, limite e configuração efetivamente
carregados. Não apague regras globais nem crie equivalência com CLAUDE.md.

Instale as skills pelo mecanismo do seu host, mantendo SKILL.md na raiz de cada pasta. Na sessão, ative
$omnx-code ou $security-auditor quando necessário. Confirme qual raiz e instruções foram lidas.
Wrapper da OMNX pode planejar execução na raiz correta sem alterar configuração global:
`python <omnx>/scripts/omnx.py --root <projeto> host codex`.

Este pacote não foi executado num Codex real. Descoberta nativa, subagentes e limites precisam de
homologação no ambiente usado. OpenAI metadata ajuda descoberta, não prova integração executada.
