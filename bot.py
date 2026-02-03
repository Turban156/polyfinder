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

# Funkce pro volání Gemini - VERZE V1 (STABILNÍ) + FLASH MODEL
def ask_gemini_direct(prompt):
    if not GEMINI_KEY:
        return "Chybí Gemini Key"
    
    # ZMĚNA: Používáme stabilní verzi 'v1' a model 'gemini-1.5-flash'
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code != 200:
            # Vypíše přesnou chybu, pokud nastane
            return f"Error {response.status_code}: {response.text}"
            
        result = response.json()
        # Bezpečné vytažení textu
        if 'candidates' in result and result['candidates']:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return "AI neodpověděla (prázdná data)."
            
    except Exception as e:
        return f"Chyba komunikace: {e}"

def get_gamma_data():
    print("Stahuji data z Polymarket Gamma API...")
    # Seřadíme podle objemu, ať máme top trhy
    url = "https://gamma-api.polymarket.com/events?limit=5&active=true&closed=false&sort=volume"
    try:
        resp = requests.get(url, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"Chyba stahování: {e}")
        return []

def parse_price(raw_prices):
    # Funkce, která vytáhne cenu ať je v jakémkoliv formátu
    try:
        # Někdy je to list ["0.55", "0.45"], někdy string
        if isinstance(raw_prices, str):
            raw_prices = json.loads(raw_prices)
        
        if isinstance(raw_prices, list) and len(raw_prices) > 0:
            val = float(raw_prices[0])
            return str(round(val, 2))
    except:
        pass
    return "0.50" # Fallback

def main():
    print("--- START BOTA (FINAL FLASH VERZE) ---")
    
    events = get_gamma_data()
    print(f"Staženo {len(events)} událostí.")

    if not events:
        print("Žádná data.")
        return

    # Zpracujeme první 3 trhy
    for i, event in enumerate(events[:3]):
        try:
            title = event.get('title', 'Bez názvu')
            
            # Získání ceny
            markets = event.get('markets', [])
            price = "Neznámá"
            
            if markets:
                main_market = markets[0] # Hlavní trh události
                price = parse_price(main_market.get('outcomePrices'))
            
            print(f"[{i+1}] {title} (Cena: {price})")

            # Analýza AI
            prompt = (f"Jsi zkušený trader. Trh: '{title}'. Cena za výsledek ANO je {price} "
                      f"(tedy šance {float(price)*100}%). "
                      f"Je to dobrá sázka? Odpověz česky, stručně, max 2 věty. Buď konkrétní.")
            
            ai_text = ask_gemini_direct(prompt)
            
            # Oříznutí textu, kdyby byl moc dlouhý
            ai_text = ai_text[:400]
            print(f"   AI: {ai_text}")

            # Odeslání na Telegram
            msg = f"🔥 *{title}*\n💵 Cena: {price}\n🤖 {ai_text}"
            send_tg(msg)
            
            print("   Odesláno. Pauza 3s...")
            time.sleep(3)

        except Exception as e:
            print(f"   Chyba cyklu: {e}")

if __name__ == "__main__":
    main()
