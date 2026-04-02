# SKILL.md — Decisões Monofloor

**Persona:** Sistema de Accountability
**Autor:** Adaptado de prompts franklimgui + Vitor Monofloor
**Versão:** 1.0

> Cole este arquivo em `/mnt/skills/user/skill-decisoes/` para ativar.

---

## 🎯 O QUE ESTA SKILL FAZ

Mantém um registro de todas as decisões importantes que você toma, com:
- Data da decisão
- Contexto e raciocínio
- Resultado esperado
- Data de revisão (30 dias depois)
- Status: pendente → revisado → sucesso/falha

---

## 📋 COMANDOS DISPONÍVEIS

### `/decidir [descrição]`
Registra uma nova decisão importante.

### `/revisar`
Lista todas as decisões com revisão pendente.

### `/resultado [id] [sucesso/falha] [comentário]`
Marca uma decisão como revisada e registra o resultado real.

### `/pendentes`
Mostra todas as decisões que ainda não foram revisadas.

### `/historico [filtro]`
Busca decisões antigas por palavra-chave.

### `/padroes`
Analisa o histórico e identifica padrões nas suas decisões.

---

## 📁 ESTRUTURA DE ARQUIVOS

```
/decisoes/
├── decisoes.csv          ← Registro principal
├── revisoes_pendentes.json  ← Cache para alertas
└── historico/
    └── 2026-Q1.csv       ← Arquivo trimestral
```

**Formato do CSV:**
```csv
id,data,decisao,categoria,contexto,resultado_esperado,riscos,revisao_em,status,resultado_real,data_revisao
```

**Categorias padrão:**
- `fornecedor` — mudanças de fornecedor
- `processo` — alterações de fluxo
- `equipe` — contratações, demissões, mudanças de função
- `financeiro` — investimentos, cortes, pricing
- `cliente` — políticas de atendimento
- `produto` — mudanças no serviço/produto

---

## 🔔 INTEGRAÇÃO COM CÉREBRO

O Cérebro Monofloor vai:
1. Ler `decisoes.csv` todas as manhãs
2. Identificar decisões com `revisao_em` = hoje
3. Enviar alerta no Telegram

---

## 📋 TRIGGERS DE ATIVAÇÃO

Ative esta skill quando o usuário mencionar:
- decidir, decisão, vou fazer, resolvi
- revisar, pendente, o que ficou
- resultado, deu certo, funcionou, falhou
- histórico, decisões antigas, padrão
- accountability, registro, documentar decisão

---

## 🔗 INTEGRAÇÃO COM OUTRAS SKILLS

- **skill-gestao**: Decisões de RH e processos
- **agente-performance**: Métricas para embasar decisões
- **estrutura-monofloor**: Contexto de fluxos afetados
- **monofloor-projetos**: Registrar decisões de projeto

---

## ⚠️ REGRAS IMPORTANTES

1. **Sempre registre o raciocínio** — não só a decisão, mas o porquê
2. **Não julgue** — sucesso/falha é dado, não opinião
3. **Mantenha simples** — uma linha por decisão
4. **Revisão é obrigatória** — decisão sem revisão não ensina nada
5. **Privacidade** — decisões sensíveis podem ser marcadas como `[privado]`
