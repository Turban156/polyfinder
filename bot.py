import os
import requests
import google.generativeai as genai
import time  # Knihovna pro čekání (aby nás Google nebloknul)
import json

# Načtení klíčů
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Nastavení AI (Flash je pro free tier ideální)
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

def get_polymarket_data():
    print("Stahuji data z Polymarketu...")
    # Použijeme stabilnější API endpoint
    url = "https://clob.polymarket.com/sampling-simplified-markets"
    try:
        resp = requests.get(url)
        data = resp.json()
        
        # Ošetření formátu dat (seznam vs slovník)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Někdy je to schované pod klíčem 'data' nebo 'markets'
            return data.get('data', list(data.values()))
        return []
    except Exception as e:
        print(f"Chyba při stahování: {e}")
        return []

def send_tg(message):
    if not TG_TOKEN or not TG_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message})
    except Exception as e:
        print(f"Chyba Telegramu: {e}")

def main():
    if not GEMINI_KEY:
        print("CHYBA: Chybí GEMINI_API_KEY!")
        return

    markets = get_polymarket_data()
    print(f"Staženo {len(markets)} trhů. Vybírám top 5 k analýze...")

    # Zpracujeme jen prvních 5, ať to netrvá věčnost
    for i, m in enumerate(markets[:5]):
        if not isinstance(m, dict):
            continue

        # 1. Získání názvu otázky (zkoušíme různé klíče)
        question = m.get('question')
        if not question:
            # Fallback, kdyby se klíč jmenoval jinak
            question = m.get('title', 'Neznámý trh')

        # 2. Získání ceny (outcomePrices bývá složitý string)
        raw_price = m.get('outcomePrices')
        price = "0.50" # Výchozí hodnota
        try:
            if isinstance(raw_price, list):
                price = raw_price[0] # Cena pro "ANO"
            elif isinstance(raw_price, str):
                # Polymarket vrací např: '["0.65", "0.35"]'
                json_prices = json.loads(raw_price)
                price = json_prices[0]
        except:
            price = m.get('lastTradePrice', 'Neznámá')

        print(f"[{i+1}/5] Analyzuji: {question} (Cena: {price})")

        # 3. Analýza s pauzou pro Free Tier
        prompt = f"Jsi trader. Trh: '{question}'. Cena za ANO: {price}. Je to v roce 2026 jasná příležitost? Odpověz 1 větou. Pokud je to super, začni slovem TIP."
        
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            print(f"   -> AI: {text}")
            
            # Pošleme na Telegram vše, co není "NIC", abyste viděl, že to funguje
            if "NIC" not in text.upper():
                send_tg(f"🤖 {question}\nCena: {price}\n{text}")
            
        except Exception as e:
            print(f"   -> Chyba AI: {e}")

        # DŮLEŽITÉ: Čekáme 5 sekund před dalším dotazem (Free Tier ochrana)
        print("   -> Čekám 5s (limit free verze)...")
        time.sleep(5)

if __name__ == "__main__":
    main()
