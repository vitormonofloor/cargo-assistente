"""
Cérebro Central — Análise híbrida (regras + AI opcional)
Executa automaticamente às 08:00 BRT via GitHub Actions

Ordem de operações:
    1. Lê dados coletados pelo agente_operacional.py
    2. Roda cerebro_regras.analisar() — 100% determinístico, sempre funciona
    3. (Opcional) Enriquece com insights via GitHub Models OU Anthropic API
    4. Envia resumo via Telegram (se configurado)

AI é cereja do bolo — o cérebro funciona 100% sem nenhuma key.
"""

import os
import json
import sys
import requests
from datetime import datetime
from pathlib import Path

# Suporta execução como módulo e como script
sys.path.insert(0, str(Path(__file__).parent))
import cerebro_regras

# ============================================================
# CONFIGURAÇÃO
# ============================================================

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

INPUT_DIR = 'outputs'
OUTPUT_DIR = 'outputs'


# ============================================================
# PROVEDORES DE AI (OPCIONAL)
# ============================================================

def tentar_enriquecer_com_github_models(analise_regras: dict, dados: dict) -> str:
    """
    GitHub Models (free tier via GITHUB_TOKEN).
    Retorna insight textual ou string vazia se falhar.
    """
    if not GITHUB_TOKEN:
        return ''

    url = "https://models.inference.ai.azure.com/chat/completions"
    headers = {
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'Content-Type': 'application/json'
    }

    prompt = (
        "Você é analista operacional da Monofloor (piso polido).\n"
        "Analise estes gargalos já identificados por regras determinísticas e "
        "gere 2-3 insights curtos (1 frase cada) em português sobre prioridades "
        "e correlações que um gestor deve notar HOJE.\n\n"
        f"Gargalos: {json.dumps(analise_regras.get('gargalos', []), ensure_ascii=False)}\n"
        f"Resumo: {analise_regras.get('resumo', '')}\n\n"
        "Seja direto. Use códigos G1/G2/G3/G4 e OE/OEC/OEI/OECT quando fizer sentido."
    )

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Você é analista sênior. Seja conciso."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 400,
        "temperature": 0.3,
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content'].strip()
        print(f"⚠️  GitHub Models retornou {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"⚠️  GitHub Models falhou: {e}")
    return ''


def tentar_enriquecer_com_anthropic(analise_regras: dict, dados: dict) -> str:
    """
    Anthropic API (fallback — só é usado se ANTHROPIC_API_KEY estiver configurada).
    """
    if not ANTHROPIC_API_KEY:
        return ''

    try:
        from anthropic import Anthropic
    except ImportError:
        print("⚠️  anthropic SDK não instalado — pulando")
        return ''

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = (
        f"Analise os gargalos já identificados e gere 2-3 insights curtos em PT-BR.\n\n"
        f"Gargalos: {json.dumps(analise_regras.get('gargalos', []), ensure_ascii=False)}\n"
        f"Resumo: {analise_regras.get('resumo', '')}"
    )

    try:
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text.strip()
    except Exception as e:
        print(f"⚠️  Anthropic falhou: {e}")
        return ''


def enriquecer_com_ai(analise_regras: dict, dados: dict) -> dict:
    """Tenta enriquecer com AI em ordem de preferência. Ignora falhas."""
    provedor_usado = None
    insight = ''

    # Prioridade 1: GitHub Models (gratuito)
    insight = tentar_enriquecer_com_github_models(analise_regras, dados)
    if insight:
        provedor_usado = 'github_models'

    # Prioridade 2: Anthropic (se houver key)
    if not insight:
        insight = tentar_enriquecer_com_anthropic(analise_regras, dados)
        if insight:
            provedor_usado = 'anthropic'

    if insight:
        analise_regras['insight_ai'] = insight
        analise_regras['ai_provedor'] = provedor_usado
        print(f"✅ AI enriqueceu análise via {provedor_usado}")
    else:
        analise_regras['ai_provedor'] = 'nenhum_disponivel'
        print("ℹ️  Sem AI disponível — usando apenas regras (modo 100% determinístico)")

    return analise_regras


# ============================================================
# TELEGRAM
# ============================================================

def enviar_telegram(mensagem: str) -> bool:
    """Envia mensagem formatada HTML para o Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ℹ️  Telegram não configurado — pulando envio")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            return True
        print(f"⚠️  Telegram retornou {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"⚠️  Erro Telegram: {e}")
    return False


def formatar_mensagem_completa(analise: dict) -> str:
    """Monta mensagem Telegram com regras + insight AI (se houver)."""
    msg = cerebro_regras.formatar_para_telegram(analise)

    insight = analise.get('insight_ai', '')
    if insight:
        provedor = analise.get('ai_provedor', 'ai')
        msg += f"\n\n🤖 <b>Insight AI</b> <i>({provedor})</i>:\n{insight}"
    else:
        msg += "\n\n<i>Modo regras — AI não disponível</i>"

    return msg


# ============================================================
# MAIN
# ============================================================

def main():
    print("🧠 Cérebro Central iniciando...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. Carregar dados operacionais
    input_file = f'{INPUT_DIR}/dados_operacionais.json'
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            dados = json.load(f)
    except FileNotFoundError:
        print(f"❌ {input_file} não encontrado — rode o agente_operacional primeiro")
        sys.exit(1)

    # 2. Análise por regras (sempre funciona)
    print("\n📐 Rodando análise por regras...")
    analise = cerebro_regras.analisar(dados)
    print(f"   Health score: {analise['health_score']}%")
    print(f"   Críticos: {analise['contadores'].get('critico', 0)}")
    print(f"   Alertas: {analise['contadores'].get('alerta', 0)}")

    # 3. Enriquecer com AI (opcional)
    print("\n🤖 Tentando enriquecer com AI...")
    analise = enriquecer_com_ai(analise, dados)

    # 4. Salvar
    output = {
        'cerebro': 'central',
        'executado_em': datetime.now().isoformat(),
        'modo': 'regras+ai' if analise.get('insight_ai') else 'regras_puras',
        'analise': analise,
    }
    output_file = f"{OUTPUT_DIR}/analise_cerebro.json"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Análise salva em {output_file}")

    # 5. Enviar Telegram (se houver algo crítico OU se configurado para sempre enviar)
    criticos = analise['contadores'].get('critico', 0)
    alertas = analise['contadores'].get('alerta', 0)

    if criticos > 0 or alertas > 0:
        print("\n📤 Enviando alerta via Telegram...")
        msg = formatar_mensagem_completa(analise)
        if enviar_telegram(msg):
            print("✅ Alerta enviado")
    else:
        print("\nℹ️  Sem gargalos — sem notificação")

    print("\n🧠 Cérebro Central finalizado!")
    return output


if __name__ == '__main__':
    main()
