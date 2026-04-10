"""
Cérebro de Regras — Análise 100% determinística, sem dependência de AI.
Lê dados coletados pelo agente_operacional.py e avalia thresholds/SLAs.

Uso:
    from cerebro_regras import analisar
    analise = analisar(dados_operacionais)

Arquitetura:
    - Thresholds configuráveis em config/thresholds.json
    - Saída compatível com cerebro_central.py (mesmo schema)
    - Retorna dict com: resumo, gargalos, alertas, recomendacoes, score
"""

import json
import os
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIGURAÇÃO
# ============================================================

SCRIPT_DIR = Path(__file__).parent.parent
CONFIG_PATH = SCRIPT_DIR / 'config' / 'thresholds.json'


def carregar_thresholds() -> dict:
    """Carrega configuração de thresholds."""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  Arquivo {CONFIG_PATH} não encontrado — usando defaults embutidos")
        return _defaults()


def _defaults() -> dict:
    """Fallback caso thresholds.json não exista."""
    return {
        "gargalos": {
            "G1_amostras_coleta": {"pipe": "oec", "fase_contem": ["solicitar coleta"], "critico": 50, "alerta": 20},
            "G2_vt_afericao": {"pipe": "oe", "fase_contem": ["vt aferição"], "critico": 30, "alerta": 15},
            "G3_aguardando_liberacao": {"pipe": "oe", "fase_contem": ["aguardando liberação"], "critico": 20, "alerta": 10},
            "G4_obras_pausadas": {"pipe": "oe", "fase_contem": ["pausa"], "critico_pct": 0.30, "alerta_pct": 0.15},
        },
        "slas_pp001": {"ciclo_medio_meta_dias": 150},
        "alertas": {"enviar_se_criticos_eq_zero": False},
    }


# ============================================================
# HELPERS
# ============================================================

def _normaliza(s: str) -> str:
    """Normaliza string para comparação case/acento-insensitive."""
    import unicodedata
    if not s:
        return ''
    n = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in n if not unicodedata.combining(c)).lower().strip()


def _fase_matches(fase_nome: str, patterns: list) -> bool:
    """Verifica se nome da fase bate com algum dos patterns."""
    fase_norm = _normaliza(fase_nome)
    return any(_normaliza(p) in fase_norm for p in patterns)


def _contar_cards_nas_fases(pipe_data: dict, patterns: list) -> tuple:
    """Retorna (total_cards_match, nomes_fases_match)."""
    fases = pipe_data.get('fases', {})
    total = 0
    nomes = []
    for nome, count in fases.items():
        if _fase_matches(nome, patterns):
            total += count
            nomes.append(f"{nome} ({count})")
    return total, nomes


# ============================================================
# REGRAS POR GARGALO
# ============================================================

def avaliar_gargalo_absoluto(gargalo_key: str, config: dict, pipe_data: dict) -> dict:
    """Gargalos com threshold em número absoluto (G1, G2, G3)."""
    total, nomes = _contar_cards_nas_fases(pipe_data, config.get('fase_contem', []))

    critico = config.get('critico', 50)
    alerta = config.get('alerta', 20)

    if total >= critico:
        nivel = 'critico'
        emoji = '🚨'
    elif total >= alerta:
        nivel = 'alerta'
        emoji = '⚠️'
    else:
        nivel = 'ok'
        emoji = '✅'

    return {
        'codigo': gargalo_key,
        'nivel': nivel,
        'emoji': emoji,
        'valor': total,
        'threshold_critico': critico,
        'threshold_alerta': alerta,
        'fases_matched': nomes,
        'descricao': config.get('descricao', ''),
        'referencia': config.get('referencia', ''),
    }


def avaliar_gargalo_percentual(gargalo_key: str, config: dict, pipe_data: dict) -> dict:
    """Gargalos com threshold em % do total de cards (G4 obras pausadas)."""
    total_pausadas, nomes = _contar_cards_nas_fases(pipe_data, config.get('fase_contem', []))
    total_pipe = pipe_data.get('total_cards', 0) or 1
    pct = total_pausadas / total_pipe

    critico_pct = config.get('critico_pct', 0.30)
    alerta_pct = config.get('alerta_pct', 0.15)

    if pct >= critico_pct:
        nivel = 'critico'
        emoji = '🚨'
    elif pct >= alerta_pct:
        nivel = 'alerta'
        emoji = '⚠️'
    else:
        nivel = 'ok'
        emoji = '✅'

    return {
        'codigo': gargalo_key,
        'nivel': nivel,
        'emoji': emoji,
        'valor': total_pausadas,
        'valor_pct': round(pct * 100, 1),
        'threshold_critico_pct': round(critico_pct * 100, 1),
        'threshold_alerta_pct': round(alerta_pct * 100, 1),
        'total_pipe': total_pipe,
        'fases_matched': nomes,
        'descricao': config.get('descricao', ''),
        'referencia': config.get('referencia', ''),
    }


# ============================================================
# ANÁLISE PRINCIPAL
# ============================================================

def analisar(dados_operacionais: dict) -> dict:
    """
    Função principal. Recebe dados coletados pelo agente_operacional.py
    e retorna análise estruturada.

    Schema de entrada esperado:
        {
            "pipefy": {
                "pipes": {
                    "oe": {"fases": {"Nome Fase": 10, ...}, "total_cards": 50},
                    "oec": {...},
                    ...
                }
            }
        }
    """
    thresholds = carregar_thresholds()
    pipes = dados_operacionais.get('pipefy', {}).get('pipes', {})

    resultado = {
        'timestamp': datetime.now().isoformat(),
        'modo': 'regras_deterministicas',
        'versao': '1.0.0',
        'gargalos': [],
        'alertas': [],
        'recomendacoes': [],
        'contadores': {'critico': 0, 'alerta': 0, 'ok': 0},
    }

    # Avaliar cada gargalo configurado
    for key, config in thresholds.get('gargalos', {}).items():
        pipe_id = config.get('pipe')
        pipe_data = pipes.get(pipe_id)

        if not pipe_data or 'erro' in pipe_data:
            resultado['gargalos'].append({
                'codigo': key,
                'nivel': 'sem_dados',
                'emoji': '❓',
                'erro': pipe_data.get('erro', 'pipe não encontrado') if pipe_data else f'pipe {pipe_id} sem dados'
            })
            continue

        # Percentual (G4) ou absoluto (G1-G3)
        if 'critico_pct' in config:
            avaliacao = avaliar_gargalo_percentual(key, config, pipe_data)
        else:
            avaliacao = avaliar_gargalo_absoluto(key, config, pipe_data)

        resultado['gargalos'].append(avaliacao)
        resultado['contadores'][avaliacao['nivel']] = resultado['contadores'].get(avaliacao['nivel'], 0) + 1

        # Gerar alerta/recomendacao
        if avaliacao['nivel'] in ('critico', 'alerta'):
            resultado['alertas'].append(_formatar_alerta(avaliacao))
            resultado['recomendacoes'].append(_gerar_recomendacao(key, avaliacao))

    # Score de saúde geral
    c = resultado['contadores']
    total_avaliados = c['critico'] + c['alerta'] + c['ok']
    if total_avaliados > 0:
        resultado['health_score'] = round((c['ok'] / total_avaliados) * 100)
    else:
        resultado['health_score'] = 0

    # Resumo executivo (regra-based, sem AI)
    resultado['resumo'] = _gerar_resumo(resultado)

    return resultado


# ============================================================
# FORMATAÇÃO DE SAÍDA
# ============================================================

def _formatar_alerta(avaliacao: dict) -> str:
    """Gera string de alerta humanizada para um gargalo."""
    codigo = avaliacao['codigo'].replace('_', ' ').title()
    if 'valor_pct' in avaliacao:
        return (
            f"{avaliacao['emoji']} {codigo}: "
            f"{avaliacao['valor']} cards ({avaliacao['valor_pct']}% do pipe) — "
            f"nível {avaliacao['nivel'].upper()}"
        )
    return (
        f"{avaliacao['emoji']} {codigo}: "
        f"{avaliacao['valor']} cards — "
        f"nível {avaliacao['nivel'].upper()} "
        f"(threshold crítico: {avaliacao['threshold_critico']})"
    )


def _gerar_recomendacao(gargalo_key: str, avaliacao: dict) -> str:
    """Recomendação padrão por tipo de gargalo."""
    mapa = {
        'G1_amostras_coleta': 'Designar responsável pela triagem e criar SLA de coleta (meta 7 dias).',
        'G2_vt_afericao': 'Revisar agenda de VT e liberar slots. Triar por data de início prevista.',
        'G3_aguardando_liberacao': 'Depende de G1 — priorizar desbloqueio das amostras para liberar cards em cascata.',
        'G4_obras_pausadas': 'Auditar motivos de pausa. Criar campo obrigatório "motivo" no Pipefy.',
    }
    return mapa.get(gargalo_key, f'Revisar processo associado a {gargalo_key}')


def _gerar_resumo(resultado: dict) -> str:
    """Resumo executivo 100% baseado em regras."""
    c = resultado['contadores']
    health = resultado.get('health_score', 0)

    if c.get('critico', 0) > 0:
        status = f"🚨 {c['critico']} gargalo(s) em nível CRÍTICO exigem ação imediata"
    elif c.get('alerta', 0) > 0:
        status = f"⚠️ {c['alerta']} gargalo(s) em nível de atenção"
    else:
        status = "✅ Operação sem gargalos críticos detectados"

    return f"{status}. Health score: {health}%. Avaliados: {sum(c.values())} indicadores."


# ============================================================
# FORMATADOR PARA TELEGRAM
# ============================================================

def formatar_para_telegram(analise: dict) -> str:
    """Formata análise para mensagem Telegram (HTML mode)."""
    msg = "🧠 <b>Cérebro Monofloor — Relatório Diário</b>\n"
    msg += f"<i>{datetime.now().strftime('%d/%m/%Y %H:%M')}</i>\n\n"

    msg += f"📋 <b>Resumo:</b>\n{analise.get('resumo', 'Sem resumo')}\n\n"

    if analise.get('alertas'):
        msg += "🚨 <b>Gargalos ativos:</b>\n"
        for a in analise['alertas'][:5]:
            msg += f"• {a}\n"
        msg += "\n"

    if analise.get('recomendacoes'):
        msg += "💡 <b>Ações recomendadas:</b>\n"
        for r in analise['recomendacoes'][:3]:
            msg += f"• {r}\n"
        msg += "\n"

    msg += f"📊 Health score: <b>{analise.get('health_score', 0)}%</b>"

    return msg


# ============================================================
# CLI / STANDALONE
# ============================================================

def main():
    """Permite rodar cerebro_regras.py standalone lendo dados_operacionais.json"""
    import sys

    input_path = sys.argv[1] if len(sys.argv) > 1 else 'outputs/dados_operacionais.json'

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
    except FileNotFoundError:
        print(f"❌ {input_path} não encontrado")
        sys.exit(1)

    analise = analisar(dados)

    # Salvar
    output_path = 'outputs/analise_regras.json'
    os.makedirs('outputs', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analise, f, ensure_ascii=False, indent=2)

    print(f"✅ Análise salva em {output_path}")
    print("\n" + "=" * 60)
    print(formatar_para_telegram(analise).replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', ''))


if __name__ == '__main__':
    main()
