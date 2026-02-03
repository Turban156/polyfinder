import os
import requests
import json
import time
import sys

# Vynucení okamžitého výpisu do logu (aby nebylo ticho)
sys.stdout.reconfigure(line_buffering=True)

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_tg(message):
    if not TG_TOKEN or not TG_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message})
    except Exception as e:
        print(f"Chyba Telegramu: {e}")

# Funkce, která zkouší různé modely
def ask_gemini_hybrid(prompt):
    if not GEMINI_KEY: return "Chybí klíč."
    
    # SEZNAM MODELŮ: První je ten nejlepší, druhý je "záchranný kruh"
    models_to_try = [
        "models/gemini-2.5-flash",  # Priorita 1: Super chytrý
        "models/gemini-1.5-flash"   # Priorita 2: Spolehlivý držák
    ]
    
    for model in models_to_try:
        print(f"   🤖 Zkouším model: {model} ...")
        url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={GEMINI_KEY}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            # Pokud narazíme na limit (429/403), jdeme hned na další model
            if response.status_code == 429 or response.status_code == 403:
                print(f"   ⚠️ Model {model} je přetížen (Limit). Přepínám na záložní...")
                time.sleep(2) # Krátký nádech
                continue # Jdeme na další model v seznamu
            
            if response.status_code != 200:
                print(f"   Chyba {response.status_code}: {response.text}")
                continue

            result = response.json()
            if 'candidates' in result and result['candidates']:
                return result['candidates'][0]['content']['parts'][0]['text']
            
        except Exception as e:
            print(f"   Chyba spojení: {e}")
            
    return "Dnes to nejde. Google stávkuje u všech modelů."

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
    print("--- START BOTA (HYBRIDNÍ VERZE) ---")
    
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
                prompt = (f"Jsi expert. Trh: '{title}'. "
                          f"Toto je složitá sázka. Napiš krátkou, vtipnou predikci. Max 2 věty.")
                icon = "🧠"
            else:
                prompt = (f"Trh: '{title}'. Šance na ANO je {price_txt}. "
                          f"Napiš k tomu jednu vtipnou glosu.")
                icon = "💰"

            # VOLÁNÍ HYBRIDNÍ FUNKCE
            ai_text = ask_gemini_hybrid(prompt)
            print(f"   AI: {ai_text}")

            msg = f"{icon} *{title}*\n📊 Stav: {price_txt}\n💬 {ai_text}"
            send_tg(msg)
            
            # Pauza 20s stačí, když máme záložní model
            print("   Odesláno. Pauza 20s...")
            time.sleep(20)

        except Exception as e:
            print(f"   Chyba: {e}")

if __name__ == "__main__":
    main()
