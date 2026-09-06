# Validação da entrega — security-auditor 2.0.0-rc.1

## Estado

Candidato a release com implementação e validação local. Não é declaração de homologação universal,
de auditoria de uma aplicação real ou de segurança garantida.

## Execução registrada

| Item | Resultado |
|---|---|
| Suíte deste pacote | **48 testes; 0 falhas; 0 erros; 0 pulados** |
| Ambiente | Python 3.13.5; Linux-6.18.35-x86_64-with-glibc2.41 |
| Registro | 2026-09-06T21:47:41.531027+00:00 |
| Resultados por caso | `test-results.json` |
| Schemas e exemplos | `schema-and-examples.json`: 30 verificações nos dois pacotes; oráculo JSON Schema independente |
| Compatibilidade estática do par | `pair-check.json`; contratos, catálogo e módulos compartilhados iguais |
| Modelo/host | Não executado; ver limites abaixo |

OMNX executou 141 testes e auditor 48. Há componentes e testes comuns; não tratar a soma como
189 cenários exclusivos de produto nem como execução dos 130 cenários de comportamento de LLM.

Os testes usam diretórios temporários e dados sintéticos. Foram verificadas transições/autorização
de Task, compare-and-swap, locks locais, parsing seguro, esquema futuro, snapshots dirty/staged,
contrato de auditoria, recibos imutáveis, separação de gates e efeitos, atualização por ZIP e
preservação de dados de fixtures na migração.
A suíte OMNX inclui fault injection em pontos de migração, rollback com edição posterior e um
subprocesso encerrado abruptamente para verificar retomada. Isso não cobre toda falha possível
de filesystem nem torna a sequência inteira uma transação atômica.

## Implementado

Núcleos condicionais, CLI local, parser YAML seguro vendorizado, schemas e validação de relações;
Task Store com autorização separada; planejamento sem mutação; aplicação/retomada/rollback por journal;
contrato de auditoria 2.0; catálogo canônico; snapshots e persistência sanitizada; avaliação local
de gates; instalação em novo destino com SHA-256; wrappers explícitos de host; testes e conjunto de evals.

A CLI do auditor não chama modelo algum nem descobre vulnerabilidades por si só. A skill instrui
o modelo hospedeiro a analisar código e evidências. O runtime valida dados e oferece ferramentas
mecânicas; `response-template` começa parcial/inconclusivo, nunca produz PASS automático.

## Não homologado / não alegado

- Nenhuma sessão real de Claude Code ou Codex foi executada. Adaptadores foram verificados por
  construção de argumentos, leitura e testes locais; descoberta, precedência, sandbox e subagentes
  reais precisam de homologação no ambiente de destino.
- Python 3.10+ é alvo de sintaxe; execução foi em 3.13.5/Linux. Windows, macOS, ACLs equivalentes,
  NFS/SMB e concorrência entre computadores não foram homologados.
- Nenhum projeto real do usuário foi migrado, nenhuma produção alterada, nenhum deploy feito,
  nenhum webhook real/Asaas/Hotmart/Supabase acionado e nenhum pentest realizado.
- Os 130 cenários de agente estão preparados, mas não executados em LLM. Não há comparação real
  de tokens/custo/latência com a skill antiga. Contagem de linhas não é benchmark de economia.
- Gates são decisões locais com evidências declaradas. Não há enforcement de CI, autenticação
  de aprovadores ou atestação independente. Hash comprova correspondência, não autoria.
- Pacotes não são assinados digitalmente. SHA-256 deve vir de origem confiada.

## Limites deliberados para preservar o usuário

Migração de linguagem natural exige mapa explícito de blocos/destinos pelo agente/revisor. O motor
não adivinha que dois requisitos são equivalentes. Original protegido no backup não substitui a
preservação de uma regra ativa: há bloqueio quando o plano não demonstra um destino coerente.

Paths perigosos, links, schemas futuros, documentos sem encoding suportado e conflitos não são
“consertados” destruindo conteúdo. Normalização semântica, colisão de nomes dependente do filesystem
ou regra customizada ambígua pode exigir resolução específica. O rollback preserva bytes e usa
permissões conservadoras; não promete restaurar toda ACL/ownership/metadata de qualquer filesystem.

Não há daemon nem update in-place que substitui toda instalação. Instale em nova pasta versionada,
valide e ative explicitamente. O host deve carregar a versão compatível; o lock sozinho não a ativa.
Não há backend externo de Tasks nem lock distribuído.

O avaliador local é conservador para exceções: não oferece bypass genérico por um JSON de “aceito”.
Uma política organizacional externa e confiável pode exigir integração adicional; não alegar que
esta integração já existe. Limites do hospedeiro sempre prevalecem.

## Reproduzir

Na raiz desta skill:

```sh
python tests/run.py --output /tmp/resultados-security-auditor.json
python scripts/auditor.py verify-package
```

O diretório de saída deve existir. `verify-package` requer o `integrity.json` incluído na distribuição;
se alterar o código, reconstrua o inventário com a ferramenta de release após testar as alterações.
O kit conjunto contém ferramentas de comparação/empacotamento e o relatório da validação após
extração dos ZIPs. Não editar resultados para aparentar que um teste foi executado.

Consulte `TRACEABILITY.md`, `LEGACY-CAPABILITIES.md` e `SOURCES.md` para cobertura, preservação
do legado e fontes consultadas. Instruções de release estão em `REPOSITORY-UPGRADE.md`.
