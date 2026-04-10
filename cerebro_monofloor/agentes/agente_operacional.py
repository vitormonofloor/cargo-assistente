"""
Agente Operacional — Coleta dados do Pipefy
Executa automaticamente às 07:30 BRT via GitHub Actions

Pipe IDs alinhados com CLAUDE.md (abr/2026):
    OE   — Ordem de Execução       (306410007)
    OEC  — Ordem de Execução Cor   (306446640)
    OEI  — Ordem de Execução Ind.  (306446401)
    OECT — Ordem de Execução Contr.(306431675)
"""

import os
import json
import sys
import requests
from datetime import datetime

# ============================================================
# CONFIGURAÇÃO
# ============================================================

PIPEFY_TOKEN = os.environ.get('PIPEFY_TOKEN')

# IDs alinhados com CLAUDE.md (fonte de verdade)
PIPES = {
    'oe':   '306410007',  # Ordem de Execução (fluxo principal)
    'oec':  '306446640',  # Ordem de Execução de Cor
    'oei':  '306446401',  # Ordem de Execução Indústria
    'oect': '306431675',  # Ordem de Execução Contratos
}

OUTPUT_DIR = 'outputs'

# ============================================================
# PIPEFY GRAPHQL
# ============================================================

def query_pipefy(query: str) -> dict:
    """Executa query GraphQL no Pipefy."""
    if not PIPEFY_TOKEN:
        return {'errors': [{'message': 'PIPEFY_TOKEN não configurado'}]}

    headers = {
        'Authorization': f'Bearer {PIPEFY_TOKEN}',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(
            'https://api.pipefy.com/graphql',
            json={'query': query},
            headers=headers,
            timeout=30
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'errors': [{'message': str(e)}]}


def get_pipe_snapshot(pipe_id: str) -> dict:
    """
    Retorna snapshot do pipe: nome, fases com contagem, total.
    Query mínima — compatível com rate limit.
    """
    query = f'''
    {{
      pipe(id: "{pipe_id}") {{
        id
        name
        phases {{
          id
          name
          cards_count
        }}
      }}
    }}
    '''
    result = query_pipefy(query)

    if 'errors' in result or not result.get('data', {}).get('pipe'):
        return {
            'pipe_id': pipe_id,
            'erro': result.get('errors', [{}])[0].get('message', 'resposta vazia'),
        }

    pipe = result['data']['pipe']
    fases = {p['name']: p['cards_count'] for p in pipe['phases']}

    return {
        'pipe_id': pipe_id,
        'pipe_name': pipe['name'],
        'fases': fases,
        'fases_detalhadas': pipe['phases'],
        'total_cards': sum(fases.values()),
    }


def coletar_dados_pipefy() -> dict:
    """Coleta snapshots de todos os pipes mapeados."""
    dados = {
        'timestamp': datetime.now().isoformat(),
        'fonte': 'pipefy',
        'pipes': {}
    }

    for nome, pipe_id in PIPES.items():
        print(f"  → Coletando {nome} ({pipe_id})...")
        dados['pipes'][nome] = get_pipe_snapshot(pipe_id)

    # Resumo agregado
    dados['resumo'] = {
        'total_pipes': len(PIPES),
        'pipes_ok': sum(1 for p in dados['pipes'].values() if 'erro' not in p),
        'pipes_erro': sum(1 for p in dados['pipes'].values() if 'erro' in p),
        'total_cards_todos_pipes': sum(
            p.get('total_cards', 0) for p in dados['pipes'].values() if 'erro' not in p
        ),
    }

    return dados


# ============================================================
# MAIN
# ============================================================

def main():
    print("🤖 Agente Operacional iniciando...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not PIPEFY_TOKEN:
        print("❌ PIPEFY_TOKEN ausente — defina via GitHub Secret")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("\n📊 Coletando dados do Pipefy...")
    dados_pipefy = coletar_dados_pipefy()

    output = {
        'agente': 'operacional',
        'executado_em': datetime.now().isoformat(),
        'pipefy': dados_pipefy,
    }

    output_file = f"{OUTPUT_DIR}/dados_operacionais.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Dados salvos em {output_file}")
    resumo = dados_pipefy.get('resumo', {})
    print(f"   Pipes OK: {resumo.get('pipes_ok')}/{resumo.get('total_pipes')}")
    print(f"   Total de cards: {resumo.get('total_cards_todos_pipes')}")
    print("🤖 Agente Operacional finalizado!")

    return output


if __name__ == '__main__':
    main()
