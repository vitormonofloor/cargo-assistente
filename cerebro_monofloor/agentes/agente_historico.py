"""
Agente Histórico — Coleta COMPLETA de cards Pipefy com phases_history.

Diferença do agente_operacional.py:
    - agente_operacional: snapshot leve (contagem por fase)
    - agente_historico:   dump detalhado com histórico de movimentação

Uso:
    export PIPEFY_TOKEN=eyJhbGci...
    python agentes/agente_historico.py

Saída: outputs/pipefy_cards_full.json — snapshot completo com:
    - id, title, created_at, phase atual
    - data_entrada (T1 — início obra, custom field)
    - data_fim (T2 — término obra, custom field)
    - phases_history: lista de { phase_id, phase_name, firstTimeIn, lastTimeOut, duration_hours }
    - metricas_temporais: T1-T0, T2-T1, T2-T0 já computados

Uso de cruzamento com Telegram:
    O JSON resultante tem campo 'title' que é o nome do cliente.
    Use esse título como palavra-chave para buscar nos grupos do Telegram.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timezone
from pathlib import Path

# ============================================================
# CONFIGURAÇÃO
# ============================================================

PIPEFY_TOKEN = os.environ.get('PIPEFY_TOKEN')
PIPE_OE = '306410007'  # Pipe OE — Ordem de Execução (fluxo principal)

OUTPUT_DIR = Path('outputs')
OUTPUT_FILE = OUTPUT_DIR / 'pipefy_cards_full.json'

# Pipefy GraphQL limita resultados por página. Vamos paginar.
PAGE_SIZE = 30
MAX_RETRIES = 3
RETRY_DELAY_S = 5
# Custom field IDs do Pipefy (descobertos via introspecção — ajuste se necessário)
FIELD_DATA_ENTRADA_CANDIDATOS = ['data_entrada', 'dataentrada', 'data_de_entrada', 'data_inicio_obra']
FIELD_DATA_FIM_CANDIDATOS = ['data_fim', 'datafim', 'data_de_fim', 'data_termino', 'data_termino_obra']


# ============================================================
# GRAPHQL
# ============================================================

def gql(query: str, variables: dict = None) -> dict:
    """Executa query GraphQL com retry."""
    if not PIPEFY_TOKEN:
        raise RuntimeError("PIPEFY_TOKEN ausente")

    headers = {
        'Authorization': f'Bearer {PIPEFY_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {'query': query}
    if variables:
        payload['variables'] = variables

    for attempt in range(MAX_RETRIES):
        try:
            r = requests.post(
                'https://api.pipefy.com/graphql',
                json=payload,
                headers=headers,
                timeout=60
            )
            if r.status_code == 200:
                data = r.json()
                if 'errors' in data:
                    print(f"⚠️  GraphQL errors: {data['errors']}")
                return data
            if r.status_code == 429:
                wait = RETRY_DELAY_S * (attempt + 1)
                print(f"⏳ Rate limit — aguardando {wait}s (tentativa {attempt+1}/{MAX_RETRIES})")
                time.sleep(wait)
                continue
            print(f"⚠️  HTTP {r.status_code}: {r.text[:200]}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Network error: {e}")
            time.sleep(RETRY_DELAY_S)

    raise RuntimeError(f"Falha após {MAX_RETRIES} tentativas")


# ============================================================
# QUERIES
# ============================================================

QUERY_CARDS_PAGINATED = """
query($pipeId: ID!, $first: Int!, $after: String) {
  cards(pipe_id: $pipeId, first: $first, after: $after) {
    pageInfo { endCursor hasNextPage }
    edges {
      node {
        id
        title
        createdAt
        finished_at
        current_phase { id name }
        fields {
          name
          value
          native_value
          field { id internal_id label type }
        }
        phases_history {
          phase { id name }
          firstTimeIn
          lastTimeOut
          duration
        }
      }
    }
  }
}
"""


def coletar_pagina(after: str = None) -> dict:
    """Coleta uma página de cards do pipe OE."""
    variables = {
        'pipeId': PIPE_OE,
        'first': PAGE_SIZE,
    }
    if after:
        variables['after'] = after

    result = gql(QUERY_CARDS_PAGINATED, variables)
    if 'data' not in result or not result['data'].get('cards'):
        return {'edges': [], 'pageInfo': {'hasNextPage': False}}
    return result['data']['cards']


def coletar_todos_cards() -> list:
    """Pagina até puxar todos os cards do pipe."""
    all_cards = []
    after = None
    page = 0

    while True:
        page += 1
        print(f"  → Página {page} (total coletado até agora: {len(all_cards)})")
        pg = coletar_pagina(after)
        edges = pg.get('edges', [])
        all_cards.extend([e['node'] for e in edges])

        info = pg.get('pageInfo', {})
        if not info.get('hasNextPage'):
            break
        after = info.get('endCursor')
        time.sleep(0.5)  # ser gentil com o rate limit

    return all_cards


# ============================================================
# EXTRAÇÃO DE CAMPOS CUSTOMIZADOS
# ============================================================

def extrair_custom_field(fields: list, candidatos: list) -> str:
    """Busca valor de campo customizado por internal_id ou label."""
    for f in fields:
        field_info = f.get('field', {}) or {}
        internal = (field_info.get('internal_id') or '').lower()
        label = (field_info.get('label') or '').lower()
        name = (f.get('name') or '').lower()

        for cand in candidatos:
            c = cand.lower()
            if c in (internal, label, name) or c in internal or c in label:
                return f.get('native_value') or f.get('value') or ''
    return ''


# ============================================================
# MÉTRICAS TEMPORAIS
# ============================================================

def parse_iso_date(s: str):
    """Parse ISO 8601 — retorna datetime ou None."""
    if not s:
        return None
    try:
        # Pipefy usa formato com Z ou offset
        s = s.replace('Z', '+00:00')
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def parse_br_datetime(s: str):
    """Parse DD/MM/YYYY HH:MM → datetime UTC."""
    if not s:
        return None
    try:
        # Pode vir só como "DD/MM/YYYY" ou "DD/MM/YYYY HH:MM"
        parts = s.strip().split(' ', 1)
        d, m, y = parts[0].split('/')
        year = int(y)
        if year < 2024 or year > 2030:
            return None
        hh, mm = (0, 0)
        if len(parts) > 1:
            try:
                hh, mm = [int(x) for x in parts[1].split(':')[:2]]
            except ValueError:
                pass
        return datetime(int(y), int(m), int(d), hh, mm, tzinfo=timezone.utc)
    except (ValueError, IndexError):
        return None


def calcular_metricas(card: dict) -> dict:
    """Computa T0, T1, T2 e as diferenças em dias."""
    fields = card.get('fields', []) or []
    t0 = parse_iso_date(card.get('createdAt'))
    t1 = parse_br_datetime(extrair_custom_field(fields, FIELD_DATA_ENTRADA_CANDIDATOS))
    t2 = parse_br_datetime(extrair_custom_field(fields, FIELD_DATA_FIM_CANDIDATOS))
    tf = parse_iso_date(card.get('finished_at'))

    def dias(a, b):
        if a and b:
            return round((b - a).total_seconds() / 86400, 1)
        return None

    return {
        't0_criacao': t0.isoformat() if t0 else None,
        't1_inicio_obra': t1.isoformat() if t1 else None,
        't2_fim_obra': t2.isoformat() if t2 else None,
        'tf_finished_at': tf.isoformat() if tf else None,
        'dias_contato_inicio': dias(t0, t1),   # T1 - T0
        'dias_execucao': dias(t1, t2),         # T2 - T1
        'dias_total': dias(t0, t2),            # T2 - T0
        'dias_admin': dias(t0, tf),            # T0 → finished_at
    }


def processar_phases_history(phases_history: list) -> list:
    """Normaliza phases_history para JSON mais limpo."""
    if not phases_history:
        return []
    out = []
    for p in phases_history:
        phase = p.get('phase', {}) or {}
        first_in = parse_iso_date(p.get('firstTimeIn'))
        last_out = parse_iso_date(p.get('lastTimeOut'))
        duracao_h = p.get('duration')
        out.append({
            'phase_id': phase.get('id'),
            'phase_name': phase.get('name'),
            'first_time_in': first_in.isoformat() if first_in else None,
            'last_time_out': last_out.isoformat() if last_out else None,
            'duracao_horas': duracao_h,
            'duracao_dias': round(duracao_h / 24, 1) if duracao_h else None,
        })
    return out


# ============================================================
# MAIN
# ============================================================

def main():
    print("🗃  Agente Histórico — coleta completa pipe OE")
    print(f"📅 {datetime.now().isoformat()}")

    if not PIPEFY_TOKEN:
        print("❌ PIPEFY_TOKEN ausente")
        sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)

    print("\n📡 Puxando cards do Pipefy (paginação)...")
    cards_raw = coletar_todos_cards()
    print(f"✅ Total coletado: {len(cards_raw)} cards")

    print("\n🧮 Processando métricas temporais...")
    cards_processados = []
    for c in cards_raw:
        metrica = calcular_metricas(c)
        phases_hist = processar_phases_history(c.get('phases_history', []))
        cards_processados.append({
            'id': c.get('id'),
            'title': c.get('title'),
            'phase_atual': (c.get('current_phase') or {}).get('name'),
            'finalizado': (c.get('current_phase') or {}).get('name') == 'CLIENTE FINALIZADO',
            **metrica,
            'phases_history': phases_hist,
            'total_fases_percorridas': len(phases_hist),
        })

    # Agregações rápidas
    finalizados = [c for c in cards_processados if c['finalizado']]
    ativos = [c for c in cards_processados if not c['finalizado']]

    def media(lista, campo):
        vals = [c[campo] for c in lista if c.get(campo) is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    resumo = {
        'coletado_em': datetime.now().isoformat(),
        'pipe_id': PIPE_OE,
        'total_cards': len(cards_processados),
        'finalizados': len(finalizados),
        'ativos': len(ativos),
        'baseline_finalizados': {
            'media_contato_inicio_dias': media(finalizados, 'dias_contato_inicio'),
            'media_execucao_dias': media(finalizados, 'dias_execucao'),
            'media_total_dias': media(finalizados, 'dias_total'),
            'media_admin_dias': media(finalizados, 'dias_admin'),
        },
        'amostras_validas': {
            'contato_inicio': sum(1 for c in finalizados if c.get('dias_contato_inicio') is not None),
            'execucao': sum(1 for c in finalizados if c.get('dias_execucao') is not None),
            'total': sum(1 for c in finalizados if c.get('dias_total') is not None),
        }
    }

    output = {
        'resumo': resumo,
        'cards': cards_processados,
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n✅ Salvo em {OUTPUT_FILE}")
    print(f"   Finalizados: {resumo['finalizados']}")
    print(f"   Ativos: {resumo['ativos']}")
    baseline = resumo['baseline_finalizados']
    if baseline['media_contato_inicio_dias']:
        print(f"   Média contato→início: {baseline['media_contato_inicio_dias']} dias")
    if baseline['media_execucao_dias']:
        print(f"   Média execução: {baseline['media_execucao_dias']} dias")
    if baseline['media_total_dias']:
        print(f"   Média journey total: {baseline['media_total_dias']} dias")


if __name__ == '__main__':
    main()
