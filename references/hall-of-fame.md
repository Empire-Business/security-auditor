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
