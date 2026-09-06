# Subir o pacote no repositório

O ZIP contém uma pasta raiz com o nome da skill. No GitHub, o conteúdo dessa pasta vai na raiz do
repositório correspondente: SKILL.md, manifest.json, references/controls, scripts, schemas, tests etc.
Não colocar omnx-code/omnx-code/SKILL.md por engano.

Trabalhe em branch/cópia recuperável. Este pacote é a nova distribuição governada da skill, não um
conjunto de instruções para concatenar ao SKILL antigo. Retire do runtime referências antigas que
concorram com o método novo, como templates equivalentes de CLAUDE e checklists universais.
Preserve .git, histórico, conteúdo do usuário e assets de site/landing que não pertencem ao runtime.
O ZIP não contém nem apaga a landing antiga; essa decisão de publicação é separada.

Verifique o diff e execute tests/run.py antes de publicar. Não rode scripts antigos de update/migration
para instalar a nova arquitetura. Adotar pacote e migrar cada aplicação são operações diferentes.
Esta distribuição não faz push nem altera visibilidade do repositório automaticamente.
