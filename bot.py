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

# Funkce pro volání Gemini - POUŽIJEME MODEL "GEMINI-PRO" (Nejspolehlivější)
def ask_gemini_direct(prompt):
    if not GEMINI_KEY:
        return "Chybí Gemini Key"
    
    # Změna: Používáme 'gemini-pro', ten funguje na v1beta nejlépe
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        # Pokud je chyba, vypíšeme ji, ale nezhroutíme se
        if response.status_code != 200:
            print(f"API Error: {response.text}")
            return "AI momentálně nedostupná."
            
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Chyba komunikace: {e}"

def get_gamma_data():
    print("Stahuji data z Polymarket Gamma API...")
    url = "https://gamma-api.polymarket.com/events?limit=5&active=true&closed=false&sort=volume"
    try:
        resp = requests.get(url, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"Chyba stahování: {e}")
        return []

def main():
    print("--- START BOTA (VERZE GEMINI-PRO) ---")
    
    events = get_gamma_data()
    print(f"Staženo {len(events)} událostí.")

    if not events:
        print("Žádná data.")
        return

    # Projdeme první 3 události
    for i, event in enumerate(events[:3]):
        try:
            title = event.get('title', 'Bez názvu')
            
            # --- OPRAVENÉ ČTENÍ CENY ---
            markets = event.get('markets', [])
            price_yes = "0.50" # Výchozí hodnota
            
            if markets:
                main_market = markets[0]
                raw_prices = main_market.get('outcomePrices')
                
                # Polymarket někdy posílá ceny jako string '["0.6", "0.4"]' a někdy jako list
                try:
                    if isinstance(raw_prices, str):
                        parsed_prices = json.loads(raw_prices)
                        price_yes = str(round(float(parsed_prices[0]), 2))
                    elif isinstance(raw_prices, list):
                        price_yes = str(round(float(raw_prices[0]), 2))
                except:
                    price_yes = "Neznámá (Odhad 0.50)"

            print(f"[{i+1}] {title} (Cena: {price_yes})")

            # Analýza AI
            prompt = (f"Jsi sázkařský analytik. Trh: '{title}'. Aktuální cena za 'ANO' je {price_yes} "
                      f"(to znamená pravděpodobnost {float(price_yes)*100 if '0.' in price_yes else 50}%). "
                      f"Je to dobrá příležitost? Odpověz stručně česky jednou větou.")
            
            ai_text = ask_gemini_direct(prompt)
            print(f"   AI: {ai_text}")

            # Odeslání
            msg = f"📊 *{title}*\n💰 Cena: {price_yes}\n🧠 {ai_text}"
            send_tg(msg)
            
            print("   Odesláno. Čekám 3s...")
            time.sleep(3)

        except Exception as e:
            print(f"   Chyba cyklu: {e}")

if __name__ == "__main__":
    main()
