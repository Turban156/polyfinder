import os
import requests
import google.generativeai as genai
import json

# Načtení klíčů
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Nastavení AI
if GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"CHYBA KONFIGURACE AI: {e}")

def send_tg(message):
    if not TG_TOKEN or not TG_CHAT_ID:
        print("!!! CHYBÍ TELEGRAM TOKENY !!!")
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        response = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message})
        print(f"Telegram status: {response.status_code}")
    except Exception as e:
        print(f"Chyba odeslání na Telegram: {e}")

def main():
    print("--- ZAČÍNÁM DIAGNOSTIKU ---")
    
    # 1. Test klíčů
    if not GEMINI_KEY: print("CHYBA: Není GEMINI KEY")
    else: print("Gemini Key: OK")
    
    if not TG_TOKEN: print("CHYBA: Není TG TOKEN")
    else: print("Telegram Token: OK")

    # 2. Stažení dat
    print("Stahuji data z Polymarketu...")
    url = "https://clob.polymarket.com/sampling-simplified-markets"
    try:
        resp = requests.get(url, timeout=10) # Timeout aby se to nezaseklo
        print(f"Status kód: {resp.status_code}")
        data = resp.json()
        
        # Výpis surových dat pro kontrolu (jen kousek)
        print(f"Typ dat: {type(data)}")
        
        market_list = []
        if isinstance(data, list):
            market_list = data
        elif isinstance(data, dict):
            market_list = data.get('data', list(data.values()))
            
        print(f"Našel jsem {len(market_list)} trhů.")
        
        if len(market_list) == 0:
            print("!!! ŽÁDNÉ TRHY K ANALÝZE !!!")
            return

        # 3. Analýza JEDNOHO trhu (pro test)
        m = market_list[0]
        print("--- DATA PRVNÍHO TRHU ---")
        print(json.dumps(m, indent=2)) # Vypíše přesnou strukturu
        
        question = m.get('question') or m.get('title') or 'Neznámý'
        print(f"Otázka: {question}")
        
        # Test AI
        print("Posílám dotaz na Gemini...")
        response = model.generate_content(f"Napiš jen slovo: FUNGUJU. Trh: {question}")
        print(f"Odpověď AI: {response.text}")
        
        # Test Telegramu
        send_tg(f"🛠 TEST BOTA: {question}\nAI: {response.text}")
        print("--- KONEC DIAGNOSTIKY ---")

    except Exception as e:
        print(f"!!! KRITICKÁ CHYBA V PROCESU: {e}")

if __name__ == "__main__":
    main()
