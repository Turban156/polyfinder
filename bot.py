import os
import requests
import google.generativeai as genai

# Načtení klíčů
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Konfigurace AI
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

def get_polymarket_data():
    print("Stahuji data z Polymarketu...")
    url = "https://clob.polymarket.com/sampling-simplified-markets"
    try:
        resp = requests.get(url)
        data = resp.json()
        
        # OPRAVA: Zpracování různých formátů dat
        market_list = []
        
        if isinstance(data, list):
            market_list = data
        elif isinstance(data, dict):
            # Pokud je to slovník, zkusíme vzít hodnoty nebo klíč 'data'
            if 'data' in data and isinstance(data['data'], list):
                market_list = data['data']
            else:
                # Polymarket někdy vrací { "id_trhu": {data}, ... }
                market_list = list(data.values())

        print(f"Zpracováno {len(market_list)} trhů.")
        return market_list[:10] # Vezmeme prvních 10
        
    except Exception as e:
        print(f"Chyba při stahování: {e}")
        return []

def send_tg(message):
    if not TG_TOKEN or not TG_CHAT_ID:
        print("Chybí Telegram tokeny, neposílám zprávu.")
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
    
    if not markets:
        print("Žádná data ke zpracování.")
        return

    print("Začínám analýzu s Gemini...")
    for m in markets:
        # Ošetření, kdyby 'm' byl jen string nebo vadný objekt
        if not isinstance(m, dict):
            continue

        question = m.get('question', 'Neznámý trh')
        # Polymarket má cenu někdy jako 'price', jindy v 'outcomePrices'
        # Zkusíme najít jakoukoliv cenu
        price = m.get('price') or m.get('lastTradePrice') or 0.5
        
        print(f"Analyzuji: {question} (Cena: {price})")

        prompt = f"Jsi analytik. Trh: '{question}'. Cena za 'ANO': {price}. Je to zajímavá sázka? Odpověz stručně. Pokud je to dobrá šance, začni slovem TIP, jinak napiš NIC."
        
        try:
            response = model.generate_content(prompt)
            ai_opinion = response.text.strip()
            
            # ZMĚNA: Pošleme vše, co není vysloveně "NIC", abychom otestovali Telegram
            if "NIC" not in ai_opinion.upper():
                msg = f"💡 {question}\nCena: {price}\n{ai_opinion}"
                send_tg(msg)
                print("-> Odesláno na Telegram.")
        except Exception as e:
            print(f"Chyba AI: {e}")

if __name__ == "__main__":
    main()
