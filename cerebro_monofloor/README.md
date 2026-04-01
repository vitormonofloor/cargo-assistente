# 🧠 Cérebro Monofloor

Sistema de inteligência automatizada para gestão operacional e financeira da Monofloor.

## 📋 Arquitetura

```
┌─────────────────┐     ┌─────────────────┐
│  🤖 Agente      │     │  🤖 Agente      │
│  Operacional    │     │  Financeiro     │
│  (07:30)        │     │  (Manual)       │
│                 │     │                 │
│  • Pipefy       │     │  • Omie (upload)│
│  • Monofloor    │     │  • D4Sign       │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
         ┌───────────────────────┐
         │   🧠 Cérebro Central  │
         │       (08:00)         │
         └───────────┬───────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │Dashboard│ │Telegram │ │  Drive  │
    │ GitHub  │ │ Alertas │ │Histórico│
    │  Pages  │ │         │ │         │
    └─────────┘ └─────────┘ └─────────┘
```

## 🚀 Como usar

### 1. Configurar Secrets no GitHub

Vá em Settings > Secrets and variables > Actions e adicione:

| Secret | Descrição |
|--------|-----------|
| ANTHROPIC_API_KEY | Chave da API Claude |
| PIPEFY_TOKEN | Token de acesso ao Pipefy |
| TELEGRAM_BOT_TOKEN | Token do Teleagente |
| TELEGRAM_CHAT_ID | ID do chat para alertas |
| GH_PAT | Personal Access Token |

### 2. Execução automática

- **07:30 BRT**: Agente Operacional extrai dados
- **08:00 BRT**: Cérebro processa e envia alertas

## 📱 Comandos Telegram

| Comando | Descrição |
|---------|-----------|
| /status | Ver status atual |
| /corrigir campo valor | Corrigir um valor |
| /aprovar | Confirmar dados OK |

## 📊 Métricas de Qualidade

| Métrica | Meta |
|---------|------|
| Taxa de acerto | ≥85% |
| Drift de margem | ≤2pp |
| Alertas úteis | ≥80% |

---
Desenvolvido para **Monofloor** | Agente de Performance
