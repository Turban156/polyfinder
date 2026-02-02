import os
import requests
import google.generativeai as genai
import json

# Načtení klíčů
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Konfigurace AI - ZMĚNA MODELU NA GEMINI-PRO (stabilnější)
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-pro')

def get_polymarket_data():
    print("Stahuji data z Polymarketu...")
    url = "https://clob.polymarket.com/sampling-simplified-markets"
    try:
        resp = requests.get(url)
        data = resp.json()
        
        market_list = []
        if isinstance(data, list):
            market_list = data
        elif isinstance(data, dict):
            if 'data' in data and isinstance(data['data'], list):
                market_list = data['data']
            else:
                market_list = list(data.values())

        print(f"Zpracováno {len(market_list)} trhů.")
        
        # DEBUG: Vypíšeme první trh, abychom viděli strukturu dat v logu
        if len(market_list) > 0:
            print("UKÁZKA DAT PRVNÍHO TRHU (pro kontrolu):")
            print(json.dumps(market_list[0], indent=2))
            
        return market_list[:5] # Pro test vezmeme jen 5, ať neplýtváme limity
        
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
    
    if not markets:
        print("Žádná data ke zpracování.")
        return

    print("Začínám analýzu s Gemini...")
    for m in markets:
        if not isinstance(m, dict):
            continue

        # Zkusíme najít otázku pod různými názvy
        question = m.get('question') or m.get('title') or m.get('slug') or 'Neznámý trh'
        
        # Zkusíme najít cenu (u simplified markets to bývá složitější)
        # Často je to v poli 'outcomePrices' jako json string
        raw_rewards = m.get('outcomePrices')
        price = "Neznámá"
        
        if raw_rewards:
            try:
                # Někdy je to string, někdy list. Zkusíme vzít první cenu.
                if isinstance(raw_rewards, list): 
                    price = raw_rewards[0]
                elif isinstance(raw_rewards, str):
                    price = raw_rewards.split(",")[0].replace('"', '').replace('[', '')
            except:
                price = "Chyba ceny"

        print(f"Analyzuji: {question} (Cena: {price})")

        # Pokud stále neznáme název trhu, přeskočíme ho, ať neplýtváme AI
        if question == 'Neznámý trh':
            print("-> Přeskakuji (chybí název)")
            continue

        prompt = f"Jsi investiční analytik. Trh: '{question}'. Aktuální cena za 'ANO': {price}. Je to zajímavá příležitost pro rok 2026? Odpověz stručně. Pokud je to dobrá šance, začni slovem TIP."
        
        try:
            response = model.generate_content(prompt)
            ai_opinion = response.text.strip()
            
            # Pošleme vše pro test, pokud to není chyba
            print(f"AI říká: {ai_opinion[:50]}...")
            if "TIP" in ai_opinion.upper() or "ANO" in ai_opinion.upper():
                msg = f"💡 {question}\nCena: {price}\n{ai_opinion}"
                send_tg(msg)
                print("-> Odesláno na Telegram.")
        except Exception as e:
            print(f"Chyba AI: {e}")

if __name__ == "__main__":
    main()
