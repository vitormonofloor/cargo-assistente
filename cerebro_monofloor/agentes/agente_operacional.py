"""
Agente Operacional - Coleta dados do Pipefy e Painel Monofloor
Executa automaticamente às 07:30 via GitHub Actions
"""

import os
import json
import requests
from datetime import datetime

# ============================================================
# CONFIGURAÇÃO
# ============================================================

PIPEFY_TOKEN = os.environ.get('PIPEFY_TOKEN')
PIPEFY_PIPE_IDS = {
    'operacoes': '302589758',
    'cores': '303420163',
    'producao': '303420513',
    'projetos': '303786498'
}

OUTPUT_DIR = 'outputs'

# ============================================================
# FUNÇÕES PIPEFY
# ============================================================

def query_pipefy(query: str) -> dict:
    """Executa query GraphQL no Pipefy"""
    headers = {
        'Authorization': f'Bearer {PIPEFY_TOKEN}',
        'Content-Type': 'application/json'
    }
    response = requests.post(
        'https://api.pipefy.com/graphql',
        json={'query': query},
        headers=headers
    )
    return response.json()


def get_cards_por_fase(pipe_id: str) -> dict:
    """Retorna contagem de cards por fase"""
    query = f'''
    {{
      pipe(id: "{pipe_id}") {{
        phases {{
          name
          cards_count
        }}
      }}
    }}
    '''
    result = query_pipefy(query)
    fases = {}
    if 'data' in result and result['data']['pipe']:
        for phase in result['data']['pipe']['phases']:
            fases[phase['name']] = phase['cards_count']
    return fases


def coletar_dados_pipefy() -> dict:
    """Coleta dados de todos os pipes"""
    dados = {
        'timestamp': datetime.now().isoformat(),
        'fonte': 'pipefy',
        'pipes': {}
    }
    
    for nome, pipe_id in PIPEFY_PIPE_IDS.items():
        try:
            fases = get_cards_por_fase(pipe_id)
            dados['pipes'][nome] = {
                'pipe_id': pipe_id,
                'fases': fases,
                'total_cards': sum(fases.values())
            }
        except Exception as e:
            dados['pipes'][nome] = {'erro': str(e)}
    
    return dados


# ============================================================
# FUNÇÕES PAINEL MONOFLOOR (placeholder para scraping)
# ============================================================

def coletar_dados_painel() -> dict:
    """
    Placeholder para scraping do Painel Monofloor
    TODO: Implementar com Playwright/Selenium
    """
    return {
        'timestamp': datetime.now().isoformat(),
        'fonte': 'monofloor_painel',
        'status': 'nao_implementado',
        'obras': []
    }


# ============================================================
# MAIN
# ============================================================

def main():
    print("🤖 Agente Operacional iniciando...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Criar diretório de output se não existir
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Coletar dados do Pipefy
    print("\n📊 Coletando dados do Pipefy...")
    dados_pipefy = coletar_dados_pipefy()
    
    # Coletar dados do Painel (placeholder)
    print("🏗️ Coletando dados do Painel Monofloor...")
    dados_painel = coletar_dados_painel()
    
    # Consolidar
    output = {
        'agente': 'operacional',
        'executado_em': datetime.now().isoformat(),
        'pipefy': dados_pipefy,
        'painel': dados_painel
    }
    
    # Salvar output
    output_file = f"{OUTPUT_DIR}/dados_operacionais.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Dados salvos em {output_file}")
    print("🤖 Agente Operacional finalizado!")
    
    return output


if __name__ == '__main__':
    main()
