import os
import requests
import json
import time
import sys

# Abychom viděli výpisy hned
sys.stdout.reconfigure(line_buffering=True)

# Načtení klíčů
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_tg(message):
    if not TG_TOKEN or not TG_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message})
    except Exception as e:
        print(f"Chyba Telegramu: {e}")

# Funkce pro volání OpenAI (GPT-4o)
def ask_openai(prompt):
    if not OPENAI_KEY:
        return "Chybí OpenAI API klíč."
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_KEY}"
    }
    
    # Nastavení modelu - gpt-4o je špička, gpt-4o-mini je levnější
    data = {
        "model": "gpt-4o", 
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code != 200:
            return f"Chyba OpenAI {response.status_code}: {response.text}"
            
        result = response.json()
        return result['choices'][0]['message']['content']
        
    except Exception as e:
        return f"Chyba komunikace: {e}"

def get_gamma_data():
    print("Stahuji data z Polymarketu...")
    url = "https://gamma-api.polymarket.com/events?limit=5&active=true&closed=false&sort=volume"
    try:
        resp = requests.get(url, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"Chyba stahování: {e}")
        return []

def main():
    print("--- START BOTA (OPENAI GPT-4o) ---")
    
    events = get_gamma_data()
    if not events:
        print("Žádná data.")
        return

    # Zpracujeme 3 události
    for i, event in enumerate(events[:3]):
        try:
            title = event.get('title', 'Bez názvu')
            markets = event.get('markets', [])
            price_txt = "Viz Polymarket"
            is_complex = False
            
            if markets:
                raw = markets[0].get('outcomePrices')
                try:
                    if isinstance(raw, str): raw = json.loads(raw)
                    if isinstance(raw, list) and len(raw) > 0:
                        val = float(raw[0])
                        if val > 0.01 and val < 0.99:
                            price_txt = f"{int(val*100)} %"
                        else:
                            price_txt = "Složitý trh"
                            is_complex = True
                except:
                    price_txt = "Neznámá"
                    is_complex = True

            print(f"[{i+1}] {title} (Cena: {price_txt})")

            # Výběr promptu
            if is_complex:
                prompt = (f"Jsi expert na predikční trhy. Trh: '{title}'. "
                          f"Toto je složitá sázka (ne jen Ano/Ne). "
                          f"Napiš krátkou (max 2 věty), chytrou a vtipnou analýzu, jak to asi dopadne.")
                icon = "🧠"
            else:
                prompt = (f"Trh: '{title}'. Pravděpodobnost 'ANO' je {price_txt}. "
                          f"Napiš k tomu jednu kousavou nebo vtipnou glosu.")
                icon = "💰"

            # Volání OpenAI
            ai_text = ask_openai(prompt)
            print(f"   GPT-4o: {ai_text}")

            msg = f"{icon} *{title}*\n📊 Stav: {price_txt}\n💬 {ai_text}"
            send_tg(msg)
            
            # U OpenAI stačí malá pauza, je rychlá
            print("   Odesláno. Pauza 5s...")
            time.sleep(5)

        except Exception as e:
            print(f"   Chyba: {e}")

if __name__ == "__main__":
    main()
