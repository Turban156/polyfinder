import os
import requests
import json
import time
import sys

# Aby se výpisy v logu objevovaly okamžitě (nečekaly v bufferu)
sys.stdout.reconfigure(line_buffering=True)

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Zůstáváme u KVALITY
MODEL_NAME = "models/gemini-2.5-flash"

def send_tg(message):
    if not TG_TOKEN or not TG_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message})
    except Exception as e:
        print(f"Chyba Telegramu: {e}")

def ask_gemini_patient(prompt):
    if not GEMINI_KEY: return "Chybí klíč."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/{MODEL_NAME}:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    # Zkusíme to až 5x (Maximální trpělivost)
    max_retries = 5
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"   🤖 Volám AI (pokus {attempt}/{max_retries})...")
            response = requests.post(url, headers=headers, json=data)
            
            # KDYŽ NÁS GOOGLE STOPNE (LIMIT)
            if response.status_code == 429 or response.status_code == 403:
                wait_time = 120 # Tvrdá pauza 2 minuty
                print(f"   ☕️ Google je přetížen. Dávám si velkou pauzu ({wait_time}s)...")
                time.sleep(wait_time)
                continue # Zkusíme to znova
                
            if response.status_code != 200:
                print(f"   Chyba API: {response.status_code}")
                time.sleep(5)
                continue
            
            # ÚSPĚCH
            result = response.json()
            if 'candidates' in result and result['candidates']:
                return result['candidates'][0]['content']['parts'][0]['text']
            
        except Exception as e:
            print(f"   Chyba spojení: {e}")
            time.sleep(10)
            
    return "Omlouvám se, Google dnes opravdu stávkuje (ani 5 pokusů nestačilo)."

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
    print("--- START BOTA (ZEN MASTER VERZE) ---")
    
    # Bezpečnostní start
    print("Zahřívám motory (10s pauza)...")
    time.sleep(10)

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

            if is_complex:
                # Expert prompt pro 2.5 Flash
                prompt = (f"Jsi špičkový krypto-analytik. Trh: '{title}'. "
                          f"Napiš k tomu jednu chytrou, analytickou a mírně vtipnou větu. "
                          f"Zapoj své znalosti o situaci.")
                icon = "🧠"
            else:
                prompt = (f"Trh: '{title}'. Šance na ANO je {price_txt}. "
                          f"Napiš k tomu jednu vtipnou glosu.")
                icon = "💰"

            # Volání s trpělivostí
            ai_text = ask_gemini_patient(prompt)
            print(f"   AI: {ai_text}")

            msg = f"{icon} *{title}*\n📊 Stav: {price_txt}\n💬 {ai_text}"
            send_tg(msg)
            
            # Pauza mezi zprávami (i když to prošlo)
            print("   Odesláno. Odpočívám 60s...")
            time.sleep(60)

        except Exception as e:
            print(f"   Chyba: {e}")

if __name__ == "__main__":
    main()
