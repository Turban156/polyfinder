import os
import requests
import google.generativeai as genai
import json
import time

# Načtení klíčů
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Nastavení AI - Použijeme 'gemini-pro', ten funguje vždy
if GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-pro')
    except Exception as e:
        print(f"CHYBA KONFIGURACE AI: {e}")

def send_tg(message):
    if not TG_TOKEN or not TG_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message})
    except Exception as e:
        print(f"Chyba Telegramu: {e}")

def get_gamma_data():
    # ZMĚNA ZDROJE DAT: Gamma API vrací čitelné názvy otázek
    print("Stahuji data z Polymarket Gamma API...")
    url = "https://gamma-api.polymarket.com/events?limit=5&active=true&closed=false&sort=volume"
    try:
        resp = requests.get(url, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"Chyba stahování: {e}")
        return []

def main():
    print("--- START BOTA (GAMMA VERZE) ---")
    
    events = get_gamma_data()
    print(f"Staženo {len(events)} událostí.")

    if not events:
        print("Žádná data.")
        return

    # Projdeme první 3 události
    for i, event in enumerate(events[:3]):
        try:
            # 1. Získání názvu (teď už tam bude!)
            question = event.get('title')
            if not question:
                continue

            # 2. Hledání ceny vnořené v datech
            markets = event.get('markets', [])
            if not markets:
                continue
            
            # Vezmeme první trh z události (hlavní otázka)
            main_market = markets[0]
            
            # Cena bývá v 'outcomePrices' jako string, např '["0.65", "0.35"]'
            raw_prices = main_market.get('outcomePrices')
            price = "Neznámá"
            
            if raw_prices:
                # Očistíme to a vezmeme první číslo (Cena pro ANO)
                price_str = str(raw_prices).replace('[', '').replace(']', '').replace('"', '').split(',')[0]
                price = str(round(float(price_str), 2)) # Zaokrouhlíme

            print(f"[{i+1}] {question} (Cena: {price})")

            # 3. Analýza AI
            prompt = f"Jsi trader. Trh: '{question}'. Cena za ANO: {price}. Je to teď v roce 2026 dobrá sázka? Odpověz 1 větou. Pokud ano, začni slovem TIP."
            
            response = model.generate_content(prompt)
            text = response.text.strip()
            print(f"   AI: {text}")

            # 4. Odeslání
            msg = f"🔮 {question}\nCena: {price}\n{text}"
            send_tg(msg)
            
            # Pauza pro Free verzi
            print("   Čekám 5s...")
            time.sleep(5)

        except Exception as e:
            print(f"   Chyba při zpracování trhu: {e}")

if __name__ == "__main__":
    main()
