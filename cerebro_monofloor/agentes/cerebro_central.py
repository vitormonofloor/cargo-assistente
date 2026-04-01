"""
Cérebro Central - Consolida dados e gera análises com Claude API
Executa automaticamente às 08:00 via GitHub Actions
"""

import os
import json
import requests
from datetime import datetime
from anthropic import Anthropic

# ============================================================
# CONFIGURAÇÃO
# ============================================================

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

INPUT_DIR = 'outputs'
OUTPUT_DIR = 'outputs'
HISTORICO_DIR = 'historico'
METRICAS_DIR = 'metricas'

# ============================================================
# FUNÇÕES DE ANÁLISE
# ============================================================

def carregar_dados_operacionais() -> dict:
    """Carrega dados coletados pelo Agente Operacional"""
    try:
        with open(f'{INPUT_DIR}/dados_operacionais.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'erro': 'Dados operacionais não encontrados'}


def analisar_com_claude(dados: dict) -> dict:
    """Envia dados para Claude e recebe análise"""
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    prompt = f'''
    Analise os dados operacionais da Monofloor e gere:
    1. Resumo executivo (3-4 frases)
    2. Gargalos identificados (fases com mais cards)
    3. Alertas críticos (se houver)
    4. Recomendações de ação
    
    Dados:
    {json.dumps(dados, ensure_ascii=False, indent=2)}
    
    Responda em JSON com as chaves: resumo, gargalos, alertas, recomendacoes
    '''
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Extrair JSON da resposta
    resposta_texto = message.content[0].text
    try:
        # Tenta parsear como JSON
        return json.loads(resposta_texto)
    except json.JSONDecodeError:
        return {'resposta_raw': resposta_texto}


# ============================================================
# FUNÇÕES DE NOTIFICAÇÃO
# ============================================================

def enviar_telegram(mensagem: str) -> bool:
    """Envia mensagem para o Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram não configurado")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")
        return False


def formatar_alerta(analise: dict) -> str:
    """Formata análise para mensagem de alerta"""
    msg = "🧠 <b>Cérebro Monofloor - Relatório Diário</b>\n\n"
    
    if 'resumo' in analise:
        msg += f"📋 <b>Resumo:</b>\n{analise['resumo']}\n\n"
    
    if 'alertas' in analise and analise['alertas']:
        msg += "🚨 <b>Alertas:</b>\n"
        for alerta in analise['alertas'][:3]:
            msg += f"• {alerta}\n"
        msg += "\n"
    
    if 'recomendacoes' in analise and analise['recomendacoes']:
        msg += "💡 <b>Ações:</b>\n"
        for rec in analise['recomendacoes'][:2]:
            msg += f"• {rec}\n"
    
    return msg


# ============================================================
# MAIN
# ============================================================

def main():
    print("🧠 Cérebro Central iniciando...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Carregar dados operacionais
    print("\n📥 Carregando dados operacionais...")
    dados = carregar_dados_operacionais()
    
    if 'erro' in dados:
        print(f"❌ {dados['erro']}")
        return
    
    # Analisar com Claude
    print("🤖 Analisando com Claude...")
    analise = analisar_com_claude(dados)
    
    # Salvar análise
    output = {
        'cerebro': 'central',
        'executado_em': datetime.now().isoformat(),
        'dados_entrada': dados,
        'analise': analise
    }
    
    output_file = f"{OUTPUT_DIR}/analise_cerebro.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Análise salva em {output_file}")
    
    # Enviar alertas
    print("\n📤 Enviando alertas...")
    mensagem = formatar_alerta(analise)
    if enviar_telegram(mensagem):
        print("✅ Alerta enviado para Telegram")
    
    print("\n🧠 Cérebro Central finalizado!")
    return output


if __name__ == '__main__':
    main()
