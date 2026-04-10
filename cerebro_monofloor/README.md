# 🧠 Cérebro Monofloor

Sistema de inteligência operacional da Monofloor.
**Funciona 100% sem AI** — usa regras determinísticas com AI opcional como cereja.

---

## 📋 Arquitetura em camadas

```
┌──────────────────────────────────────────────────┐
│   CAMADA 1 — COLETA (Agente Operacional)         │
│   07:30 BRT · Pipefy GraphQL · só PIPEFY_TOKEN   │
└────────────────────┬─────────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────┐
│   CAMADA 2 — REGRAS (cerebro_regras.py)          │
│   Análise determinística · thresholds.json       │
│   Nenhuma dependência externa                    │
└────────────────────┬─────────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────┐
│   CAMADA 3 — AI OPCIONAL (cerebro_central.py)    │
│   1º: GitHub Models (FREE via GITHUB_TOKEN)      │
│   2º: Anthropic API (fallback se houver secret)  │
│   Se ambos faltarem: skip, regras já bastam      │
└────────────────────┬─────────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────┐
│   CAMADA 4 — NOTIFICAÇÃO                         │
│   Telegram (opcional) · só se houver gargalos    │
└──────────────────────────────────────────────────┘
```

### Princípio de design

**"AI é cereja do bolo, não ingrediente"** — se a Anthropic API cair, o Cérebro
continua gerando alertas via regras. Se o GitHub Models não estiver disponível,
a Anthropic cobre. Se as duas falharem, o relatório rule-based já é acionável.

---

## 🚀 Como usar

### Secrets obrigatórios

Vá em **Settings → Secrets and variables → Actions**:

| Secret | Obrigatório? | Descrição |
|---|---|---|
| `PIPEFY_TOKEN` | ✅ Sim | Token Pipefy (coleta de dados) |

### Secrets opcionais

| Secret | Descrição |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot do Teleagente — envia alertas |
| `TELEGRAM_CHAT_ID` | Chat ID do Vitor (`8151246424`) |
| `ANTHROPIC_API_KEY` | Só se quiser AI adicional — **não é mais obrigatório** |

### GitHub Models (grátis, sem cadastro)

O workflow já pede `permissions: models: read` no `.github/workflows/cerebro.yml`.
Isso dá acesso automático ao endpoint `https://models.inference.ai.azure.com`
usando o `GITHUB_TOKEN` que o Actions já possui. **Zero configuração adicional.**

Modelo padrão: `gpt-4o-mini` — trocável em `config/thresholds.json`.

---

## 🗂️ Estrutura de arquivos

```
cerebro_monofloor/
├── agentes/
│   ├── agente_operacional.py  ← coleta Pipefy (pipe IDs corretos)
│   ├── agente_d4sign.py       ← contratos D4Sign
│   ├── cerebro_regras.py      ← motor de regras (sem AI)
│   └── cerebro_central.py     ← orquestrador (regras + AI opcional)
├── config/
│   ├── cerebro_config.json    ← config geral
│   └── thresholds.json        ← thresholds G1-G4 (editável sem código)
├── outputs/                    ← gerado em cada run
│   ├── dados_operacionais.json
│   └── analise_cerebro.json
└── README.md
```

---

## ⚙️ Configuração dos thresholds

Edite `config/thresholds.json` — nenhum deploy necessário.

```json
{
  "gargalos": {
    "G1_amostras_coleta": {
      "pipe": "oec",
      "fase_contem": ["solicitar coleta"],
      "critico": 50,
      "alerta": 20
    }
  }
}
```

**Sistema de matching de fases**: a lista `fase_contem` é comparada contra os
nomes das fases do Pipefy de forma case-insensitive e sem acentos. Qualquer
match parcial ativa a contagem.

---

## 🏃 Rodar localmente

```bash
cd cerebro_monofloor

# 1. Coletar dados
export PIPEFY_TOKEN=eyJhbGci...
python agentes/agente_operacional.py

# 2. Rodar análise por regras (sempre funciona)
python agentes/cerebro_regras.py outputs/dados_operacionais.json

# 3. Rodar análise completa (regras + AI opcional + Telegram)
export GITHUB_TOKEN=ghp_...                     # opcional
export TELEGRAM_BOT_TOKEN=...                   # opcional
export TELEGRAM_CHAT_ID=8151246424              # opcional
python agentes/cerebro_central.py
```

---

## 📊 Gargalos monitorados

| Código | Nome | Pipe | Threshold crítico |
|---|---|---|---|
| **G1** | Amostras em Solicitar Coleta | OEC | 50 cards |
| **G2** | Agend. VT Aferição | OE | 30 cards |
| **G3** | Aguardando Liberação | OE | 20 cards |
| **G4** | Obras Pausadas | OE | 30% do pipe |

**SLAs PP:001** (Data X = Início da obra):
- VT Aferição: X−60d
- Escolha da Cor: X−35d
- VT Entrada: X−10d
- Definir Equipe: X−7d

---

## 🔄 Migração da versão anterior

**O que mudou:**

| Antes | Depois |
|---|---|
| Dependia 100% de `ANTHROPIC_API_KEY` | Funciona sem nenhuma AI |
| Pipe IDs errados (302589758...) | Alinhados com CLAUDE.md (306410007...) |
| Sem regras determinísticas | `cerebro_regras.py` cobre 7/9 indicadores |
| Prompt ao Claude em cada run | AI só enriquece, não é crítica |
| `if: always()` duplicado no YAML | Workflow consolidado |
| Sem free tier de AI | GitHub Models (`gpt-4o-mini`) grátis |

**Impacto**: Cérebro funcional hoje mesmo, sem precisar criar conta Anthropic.

---

Desenvolvido para **Monofloor** | Abril 2026
