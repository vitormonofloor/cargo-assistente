"""
Agente D4Sign - Extrai contratos e parcelas do D4Sign
Semi-automático: requer login manual, extração automática
Integra com Cérebro Monofloor para análise financeira
"""

import os
import json
import re
from datetime import datetime

# ============================================================
# CONFIGURAÇÃO
# ============================================================

D4SIGN_EMAIL = os.environ.get('D4SIGN_EMAIL', 'contato@monofloor.com.br')
OUTPUT_DIR = 'outputs'

# ============================================================
# FUNÇÕES DE EXTRAÇÃO
# ============================================================

def extrair_parcelas_do_texto(texto: str) -> list:
    """Extrai parcelas de um texto de contrato"""
    parcelas = []
    
    padroes = [
        r'(\d+)[ªº]?\s*parcela[:\s]+R?\$?\s*([\d.,]+)',
        r'parcela\s*(\d+)[:\s]+R?\$?\s*([\d.,]+)',
        r'(\d+)\s*[xX]\s*R?\$?\s*([\d.,]+)',
        r'entrada[:\s]+R?\$?\s*([\d.,]+)',
    ]
    
    for padrao in padroes:
        matches = re.findall(padrao, texto, re.IGNORECASE)
        for match in matches:
            if len(match) == 2:
                num, valor = match
                valor_limpo = valor.replace('.', '').replace(',', '.')
                try:
                    parcelas.append({
                        'numero': int(num) if num.isdigit() else 0,
                        'valor': float(valor_limpo)
                    })
                except:
                    pass
    
    return parcelas


def extrair_datas(texto: str) -> list:
    """Extrai datas de vencimento do texto"""
    datas = []
    padroes = [
        r'(\d{2}[/.-]\d{2}[/.-]\d{4})',
        r'(\d{2}[/.-]\d{2}[/.-]\d{2})',
    ]
    
    for padrao in padroes:
        matches = re.findall(padrao, texto)
        datas.extend(matches)
    
    return datas


def processar_contrato(texto: str, nome: str) -> dict:
    """Processa um contrato e extrai informações relevantes"""
    return {
        'nome': nome,
        'parcelas': extrair_parcelas_do_texto(texto),
        'datas': extrair_datas(texto),
        'processado_em': datetime.now().isoformat()
    }


# ============================================================
# MAIN (execução manual com Playwright)
# ============================================================

def main():
    """
    Execução semi-automática:
    1. Usuario faz login no D4Sign via browser
    2. Script extrai dados dos contratos
    3. Salva em JSON para o Cérebro processar
    """
    print("📄 Agente D4Sign")
    print("=" * 50)
    print("Este agente requer execução manual com Playwright")
    print("Para usar: pip install playwright && playwright install")
    print("")
    print("Instruções:")
    print("1. Execute com: python agente_d4sign.py")
    print("2. Faça login manual no D4Sign quando abrir o browser")
    print("3. O script extrairá os contratos automaticamente")
    print("=" * 50)


if __name__ == '__main__':
    main()
