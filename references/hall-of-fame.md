# Hall of Fame — Red Team da própria skill (v1.9)

Em 2026-07-10, a skill `security-auditor` foi submetida a um **red-team contra si mesma**: 6 agentes atacantes independentes, cada um com um vetor distinto, competindo para achar falhas na metodologia, cobertura, conselhos e garantias da skill. Esta versão (v1.9) incorpora as correções.

## Método de pontuação
- P0 = 3 pts, P1 = 2 pts, P2 = 1 pt; **+1** por falha-bandeira original e devastadora.
- ~120 achados brutos foram deduplicados em ~89 falhas únicas; cada uma atribuída ao dono com a melhor prova (`arquivo:linha` + originalidade).
- Achado vago, duplicado ou sem prova = 0. Qualidade > volume bruto.

## Pódio

### 🥇 AGENTE 2 — "O Auditor de Correção" (39 pts)
*Caçador de conselho errado/perigoso, com fact-checking externo.*
- **RPC "seguro" virava roubo de saldo + auto-crédito** (`audit-details.md` `process_purchase`): função pública, sem `auth.uid()`, sem `amount>0`, valor negativo invertia o sinal.
- **Tabela de CVE marcava Next vulnerável (React2Shell) como seguro** (CVE-2025-66478 omitia 15.0/15.2–15.5).
- AAL de MFA derivado de `factors.length`; hook RBAC sem `SECURITY DEFINER`; LGPD "72h"; CSRF `origin.includes`.

### 🥈 AGENTE 6 — "O Explorador de Lógica & Borda" (32 pts)
*Falhas que IA de vibe-coding introduz e checklists não pegam.*
- **Teste de IDOR da skill esperava `403`, mas RLS devolve `200`/vazio** — falso positivo em toda auditoria (sistêmico).
- Mass-assignment na camada de privilégio; multi-tenant sem teste A→B; Unicode/homógrafos; float em dinheiro; races de estoque/voto/like; upload (polyglot/SVG/zip-slip/limite decodificado).

### 🥉 AGENTE 5 — "O Atacante da Própria Skill" (29 pts)
*A skill como artefato de supply-chain e prompt privilegiado.*
- **`git pull origin main` sem assinatura = RCE em massa** da base de usuários.
- Fase 2 roda `npm run` do alvo (RCE/exfil de `.env`); zero anti-prompt-injection; "corrija" auto-aplica `REVOKE/ALTER/DELETE/filter-repo`.

## Menção honrosa (empate, 28 pts)
- **AGENTE 3 — "O Cético do Processo"**: VERIFICAR = grep; SQL (núcleo RLS/MFA) nunca re-verificado no banco; Fase 2 não prova segurança; sem threat model/ASVS; sem scanners reais.
- **AGENTE 4 — "O Expansionista de Escopo"**: **IA/LLM totalmente ausente**; Edge/Deno; ORMs que bypassam RLS; CI/CD posture; monorepo; compliance além de LGPD.

## Participação
- **AGENTE 1 — "O Bypassador" (26 pts)**: maior volume bruto; achados únicos `x-forwarded-for` spoofável (anula rate-limit e auto-bane vítimas no honeypot), cache/ISR de dados autenticados, OAuth/PKCE, refresh-rotation, HIBP, subdomain takeover.

## Como o resultado virou código
Os achados do top 3 viraram o núcleo da v1.9 (ver `CHANGELOG.md`): correção dos exemplos errados, verificação real, Passo 0 de threat model, novos módulos (`references/v19-modules.md`) e Guardrails v2 com supply-chain assinado da própria skill.

---

# Rodada 2 — Red Team da INTEGRAÇÃO omnx-code ⇄ security-auditor (v1.10)

Em 2026-07-10, 4 agentes atacaram a **costura** entre as duas skills (não a auditor por dentro). Veredito convergente: o endurecimento v1.9 era **declarado, não imposto** — o "gate" vivia em checkboxes e o "update assinado" não tinha no que pinnar. A v1.10 incorpora as correções (gate real via `verdict.json` fail-closed, update verify-antes, anti-downgrade de instalações irmãs).

## Método de pontuação
- P0 = 5, P1 = 3, P2 = 2, P3 = 1; **×2** por achado único, **×1** por compartilhado; bônus por verificação empírica (git/symlink).
- 1º–2º e 3º–4º ficaram muito próximos; o pódio privilegia achados únicos de maior impacto na integração.

## Pódio

### 🥇 Inspetor de Pipeline
- **Bypass via agentes externos**: `AGENTS.md` (lido por Lovable/Cursor/Codex) nunca citava a `/security-auditor` nem o gate → push→main→Vercel sem saber do bloqueio.
- **Fail-open por política** (`omnx-code/SKILL.md`: "não bloqueie, deixe o usuário decidir"); re-teste aberto (o fix já deploya); momentos ausentes (merge em main, rotação de secrets, troca Supabase); mismatch de severidade/status no handoff.

### 🥈 Atacante da Supply-Chain (verificação empírica)
- **Sombra `~/.agents` (v1.4/v1.7 com RCE cego) sem detecção** — a v1.9 endurecida era contornada se qualquer runtime lesse `~/.agents`.
- **`git checkout <ref> && git verify-tag … || echo` aplicava ANTES de verificar**; `git tag` vazio e HEAD não assinado → `git pull` com teatro. Path hardcoded + symlink quebrado em `~/.codex`; anti-prompt-injection só do lado da auditor.

### 🥉 Operador Cínico
- **Colisão de triggers** ("atualiza a skill" / "auditar segurança" sem dono); **self-rewrite em plena execução** (checkout de si mesma como Task 1 e segue sem reload); **single-source-of-truth violada** (checklist da omnx codificava política de segurança). Foi o único a recusar overclaim.

## Menção honrosa
- **Advogado do Contrato**: mapeou a base estrutural — sem tags, sem schema de saída, sem `version` no frontmatter, semver lexicográfico, e a contradição de auto-fix no corpo da auditor.

## Como o resultado virou código (v1.10)
`security-report/verdict.json` + gate fail-closed na omnx-code (recusa push/merge sem `gate: PASS`); `version`/`contract_version` nos frontmatters; update `git verify-tag && git checkout` (verificar antes), sem `|| echo`, sem `--ff-only`, com allowlist/SHA e `curl -fsSL`; Passo 0 de varredura de instalações irmãs; gate espelhado no `AGENTS.md`; self-update por último + reload; copy honesta.

---

# Aprendizado incorporado — Incidente real Shai-Hulud (npm supply-chain worm)

Diferente das rodadas de red-team internas, este aprendizado veio de um incidente real do ecossistema npm (Shai-Hulud, 2025-2026), não de ataque simulado contra a própria skill.

## O que aconteceu
O worm comprometeu contas de mantenedores npm legítimos e publicou versões maliciosas com scripts `postinstall` que roubavam tokens (npm, GitHub, cloud), usando-os para se auto-publicar em novos pacotes da própria vítima — replicação em cadeia sem depender de CVE nova.

## Gap que isso expôs
Até v1.10, §6/§22b cobriam CVE catalogada, lockfile commitado e `npm ci` — mas não instruíam a procurar indicadores de comprometimento tipo worm quando não há CVE formal.

## Como virou código
- §6b — critério de severidade para staleness
- §6c — janela de 90 dias pós-disclosure via GHSA/OSV.dev, padrão suspeito de publish/maintainer
- §6d (P0) — IoC de worm: postinstall suspeito, maintainer novo sem justificativa, lockfile drift, transitivas não auditadas
- `references/infrastructure.md` → checklist de IoC tipo worm
- Escopo mantido complementar ao omnx-code (regra 15): instalação fica lá, auditoria de projeto existente fica aqui.
