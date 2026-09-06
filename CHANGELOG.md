# Changelog

## 2.0.0-rc.1 — 2026-09-06

Recriação coordenada baseada na especificação v4. Release candidate implementada e testada localmente.

- Núcleos pequenos e referências condicionais; AGENTS.md único no método.
- Três eixos UX/S/O, mockup histórico sem sincronização e auditoria delimitada.
- Task Store com autorização explícita, CAS, dependências e arquivamento por ID.
- Migração semântica planejada com aplicação mecânica, snapshot, journal, resume e rollback.
- Contrato 2.0, catálogo de 31 controles, recibos imutáveis e gates locais.
- Distribuição offline por digest em diretório novo; sem download/execução/deploy automáticos.
- Testes determinísticos e de injeção de falha; matriz de evals comportamentais separada.

Não inclui homologação em Claude/Codex reais, benchmarks de tokens de modelos, pentest de aplicação
ou integração de CI independente. Consulte reports/VALIDATION.md para os resultados da construção.
