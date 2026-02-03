import os
import requests
import json
import time

# Načtení klíčů
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_tg(message):
    if not TG_TOKEN or not TG_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message})
    except Exception as e:
        print(f"Chyba Telegramu: {e}")

# Funkce pro volání Gemini PŘÍMO (bez knihovny)
def ask_gemini_direct(prompt):
    if not GEMINI_KEY:
        return "Chybí Gemini Key"
    
    # Použijeme model Flash (je zdarma a rychlý)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            return f"Chyba API: {response.text}"
            
        result = response.json()
        # Vytáhneme text z JSON odpovědi
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Chyba komunikace s AI: {e}"

def get_gamma_data():
    print("Stahuji data z Polymarket Gamma API...")
    # Seřadíme podle objemu peněz (volume), ať máme ty nejpopulárnější
    url = "https://gamma-api.polymarket.com/events?limit=5&active=true&closed=false&sort=volume"
    try:
        resp = requests.get(url, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"Chyba stahování: {e}")
        return []

def main():
    print("--- START BOTA (DIRECT API VERZE) ---")
    
    events = get_gamma_data()
    print(f"Staženo {len(events)} událostí.")

    if not events:
        print("Žádná data.")
        return

    # Projdeme první 3 události
    for i, event in enumerate(events[:3]):
        try:
            title = event.get('title', 'Bez názvu')
            
            # Hledání ceny (vylepšené)
            markets = event.get('markets', [])
            if not markets:
                continue
            
            main_market = markets[0]
            raw_prices = main_market.get('outcomePrices')
            
            # Gamma vrací ceny jako list stringů ["0.65", "0.35"]
            price_yes = "Neznámá"
            if raw_prices and isinstance(raw_prices, list) and len(raw_prices) > 0:
                price_yes = str(round(float(raw_prices[0]), 2))
            
            print(f"[{i+1}] {title} (Cena: {price_yes})")

            # Analýza AI (přímo)
            prompt = f"Jsi expert na sázky. Trh: '{title}'. Cena za ANO je {price_yes}. Je to podle tebe výhodná sázka? Odpověz česky, maximálně 2 věty."
            
            ai_text = ask_gemini_direct(prompt)
            print(f"   AI: {ai_text}")

            # Odeslání
            msg = f"📊 *{title}*\n💰 Cena ANO: {price_yes}\n🤖 AI: {ai_text}"
            send_tg(msg)
            
            print("   Odesláno. Čekám 3s...")
            time.sleep(3)

        except Exception as e:
            print(f"   Chyba cyklu: {e}")

if __name__ == "__main__":
    main()
