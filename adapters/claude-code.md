# Claude Code sem CLAUDE.md

Somente AGENTS.md é canônico. Na ativação explícita da OMNX, leia o arquivo confiável pertinente antes
da operação; isso cobre a execução atual, não garante todas as sessões futuras.

CLI documenta --append-system-prompt-file. O wrapper da OMNX pode planejar argv sem executar:
```sh
python <omnx>/scripts/omnx.py --root <projeto> host claude
```
Execução explícita (flags do wrapper antes do nome do host devido ao passthrough):
```sh
python <omnx>/scripts/omnx.py --root <projeto> host --execute --trust-root \
  --expected-agents-sha256 <hash-atual-confiado> claude
```
O wrapper preserva o prompt padrão, não cria arquivo CLAUDE.md, não instala hooks globais e recusa
flags conhecidas de substituição de prompt/bypass. Não é sandbox para todas as flags da CLI.
Só promova AGENTS de raiz confiada, nunca conteúdo de PR não confiável para ganhar autoridade.

Teste local do wrapper usa host simulado. Claude real, versão instalada, tool permissions e subagentes
não foram executados no ambiente de entrega. Valide no seu host e registre a versão antes de anunciar automático.
