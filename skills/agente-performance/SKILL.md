---
name: agente-performance
description: >
  PERSONA ATIVA: Agente de Performance Geral da Monofloor.
  Responsável por construir, manter e evoluir a Régua de Saúde Operacional e o
  Centro de Projetos — plataforma de margem real por obra.
  Quando acionado, apresente-se e retome o contexto sem pedir nenhum arquivo.
  Todo o histórico está aqui nesta skill.
  Ative para: régua de saúde, performance, indicadores, dashboard, metas, métricas,
  visão macro, calibrar projetos, agente de performance, saúde operacional,
  centro de projetos, custo por projeto, margem por projeto, D4Sign, Omie,
  planilha financeira, contas a pagar, custo operacional, devoluções, Pipefy,
  throughput, ciclo médio, taxa de pausa, ticket médio, NPS, margem.
---

# PERSONA: Agente de Performance Geral — Monofloor

## Apresentação ao ser ativado

> "Olá, Vitor! Aqui é o **Agente de Performance Geral** da Monofloor.
> Meu papel é manter, evoluir e calibrar a **Régua de Saúde Operacional** e o
> **Centro de Projetos** — plataforma de margem real por obra.
> Última sessão: 27/03/2026. Retomo o contexto direto!"

---

## ENTREGÁVEIS PUBLICADOS

| Item | URL | Status |
|------|-----|--------|
| Dashboard Régua de Saúde | https://vitormonofloor.github.io/cargo-assistente/dashboard.html | v2.0 ativo |
| Centro de Projetos | https://vitormonofloor.github.io/cargo-assistente/projetos.html | Camada 1+2 ativo |
| Repositório GitHub | vitormonofloor/cargo-assistente | ativo |

**GitHub token:** salvo na skill teleagente-monofloor (campo "GitHub Token")
**Atualização:** via API GitHub no browser (PUT /contents/<arquivo> com SHA + base64)

---

## PROJETO CENTRO DE PROJETOS — ESTADO ATUAL (27/03/2026)

### Arquitetura em 3 camadas

| Camada | Fonte | Status |
|--------|-------|--------|
| 1 — Custos | Planilhas Omie (Matriz + Filial + Mineral) | COMPLETO |
| 2 — Dados de obra | Pipefy GraphQL (m², fase, datas) | COMPLETO |
| 3 — Receita | D4Sign (valor dos contratos por cliente) | PENDENTE |

---

### CAMADA 1 — CUSTOS (COMPLETO)

Arquivos carregados: Contas_a_pagar_MATRIZ_janeiro-26.xlsx, FILIAL e MINERAL

- Matriz: 316 lançamentos, R$ 571.286
- Filial: 928 lançamentos, R$ 779.201
- Mineral: 8 lançamentos, R$ 5.436
- **Total: R$ 1.355.923 | 1.252 lançamentos | 156 projetos**

**Devoluções (cat. 14.x) — NÃO são custo operacional: R$ 170.263**
- TGSJ Empreendimentos: R$ 119.901
- Gabriela Guarita Dirani: R$ 40.077
- R3 PR + outros: ~R$ 10.285

**Custo operacional real: R$ 1.185.660**

**MATA-METRO — ponto crítico:**
R$ 778.486 (65,6% do total) em um único item — guarda-chuva de pagamentos de
prestadores sem projeto-destino. Não existe como card individual no Pipefy.
Ação futura: rateio por projeto real cruzando prestadores e datas.

**Top categorias:**
- Prestadores de aplicação: R$ 690.218 (58%)
- Hotel viagem: R$ 69.170
- Km rodados obra: R$ 56.637
- Materiais de consumo: R$ 51.627
- Deslocamento: R$ 48.383
- Comissões RT (arquitetos): R$ 46.927

---

### CAMADA 2 — PIPEFY (COMPLETO)

Extração via GraphQL API (token salvo em teleagente-monofloor).
- 591 cards extraídos do pipe OE (306410007)
- Campos: nome_projeto, M2 TOTAL, fase, created_at, finished_at, DATA DE FINALIZACAO
- 434 cards com m2 preenchido | 591 com nome | 458 com datas

**Match com planilha financeira (top 51 projetos):**
- 45/51 projetos matched (88%)
- 39 com m2 disponível
- Sem match: MATA-METRO, Industria Boqueirão, Livia Ribeiro, AVVA House, Paula Waldvogel, Amanda Hannud 2a Fase

**Destaques por R$/m2 de custo:**
- Luis Gustavo Rovaron: R$ 485/m2 — ALERTA (m2 pequeno vs custo alto)
- Iolanda Odebrecht: R$ 186/m2 — normal
- Marcos Veiga Gomes: R$ 188/m2 — normal
- Amendoeiras (SPE): R$ 59/m2 em OBRA PAUSADA desde jul/25
- Casa Vik: R$ 1/m2 — m2 suspeito (615m2 registrado)

---

### CAMADA 3 — D4SIGN / RECEITA (PENDENTE)

**O que falta:** valor do contrato por projeto = receita bruta

**Status:** 100 documentos listados (5 paginas x 20) via fetch das paginas HTML
Cofre D4Sign: https://secure.d4sign.com.br/desk/cofres/216934/af02a7f2-111a-4a5f-b526-56072a4f5d01.html

**Como continuar na proxima sessao:**
1. Abrir o cofre D4Sign (sessao ativa no browser do Vitor)
2. Para cada UUID, abrir /desk/viewblob/{uuid}?doc_show=1 e extrair valor via regex
3. Padrao a buscar: "R$ X.XXX,XX" ou "valor total" no texto do PDF renderizado
4. Cruzar nome do cliente no contrato com projeto na planilha financeira

**Amostra dos primeiros contratos listados (pag. 1):**
- 59b121b0 — UNKE ARQUITETURA E ENGENHARIA LTDA — 24/Mar/2026
- 1b7b2ff5 — EUROPRESTIGIO DISTRIBUICAO E COMERCIO LTDA — 24/Mar/2026
- bfba02bb — CARLA ANTONIO - CONTRATO MONOFLOOR — 24/Mar/2026
- 5eca6685 — ADRIANA RUTH ADLER - CONTRATO MONOFLOOR — 24/Mar/2026
- 1589bb37 — BRUNO HENRIQUE LOPEZ LIMA - CONTRATO MONOFLOOR — 23/Mar/2026
- (+ ~95 contratos em paginas 2 a 5)

---

## PENDENCIAS EM ORDEM DE PRIORIDADE

### PROXIMA SESSAO (alta prioridade)
1. Extrair receita do D4Sign — iterar UUIDs, abrir contratos, capturar valor
2. Calcular margem real por projeto (receita - custo)
3. Atualizar plataforma projetos.html com coluna receita e margem

### CURTO PRAZO
4. Resolver MATA-METRO — metodologia de rateio dos R$ 778k
5. Adicionar meses seguintes (Feb/Mar 2026) para tendencia
6. Cruzar indenizacoes (R$ 24k) com projetos para identificar recorrencia

### MEDIO PRAZO
7. Alimentar Regua de Saude com dados de margem real apurados
8. Acesso ao Omie para DRE completo (folha, overhead, margem liquida)
9. Automatizar atualizacao mensal

---

## REGUA DE SAUDE OPERACIONAL — ESTADO ATUAL

8 setores, 57 indicadores — dashboard publicado em v2.0

**Criticos ativos:**
- SLA VT Afericao: 3% vs meta 90%
- Taxa de pausa: 47,6% vs meta 10%
- Ciclo medio: 238 dias vs meta 150 dias
- Amostras G1 (coleta): 267 vs meta 20
- NPS: processo inexistente
- Pos-obra Pipefy: 0 cards

---

## DADOS BASE — CONTRATOS D4SIGN (historico anterior)

- 8 contratos 2025: total R$644.630 | ticket medio R$80.578 | m2 medio 102m2
- 8 contratos 2026 (amostra): total R$1.207.084 | ticket medio R$150.885 | m2 medio 155m2
- Variacao YoY: +87,3%
- Mix 2026: 50% fora de base (ticket R$216.808) vs 50% base (R$84.963)

## TABELA DE PRECOS 2026

| Produto | Parcelado |
|---------|-----------|
| Stelion Piso | R$ 637/m2 |
| Lilit Piso | R$ 560/m2 |
| Lilit Parede | R$ 448/m2 |
| Stelion Parede | R$ 728/m2 |
| Stelion Bancada | R$ 1.365/m2 |

---

## COMO RETOMAR NA PROXIMA SESSAO

1. Ler esta skill — tudo esta aqui
2. Centro de Projetos ja publicado com Camadas 1+2 em projetos.html
3. Proximo passo: Camada 3 (D4Sign) — abrir cofre, iterar UUIDs, extrair valores
4. Token GitHub e Pipefy: ver skill teleagente-monofloor
