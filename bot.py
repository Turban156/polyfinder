import os
import requests
import json
import time
import sys

# Vynucení okamžitého výpisu do logu
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

# OPRAVENÁ HYBRIDNÍ FUNKCE
def ask_gemini_hybrid(prompt):
    if not GEMINI_KEY: return "Chybí klíč."
    
    # DEFINICE MODELŮ A JEJICH ADRES
    # 1. Priorita: Gemini 2.5 (Super chytrý) - je na adrese v1beta
    # 2. Záloha: Gemini 1.5 Flash (Spolehlivý) - je na adrese v1 (STABILNÍ)
    
    configs = [
        {
            "name": "Gemini 2.5 Flash (Beta)",
            "url": f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
        },
        {
            "name": "Gemini 1.5 Flash (Stable)",
            "url": f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        }
    ]
    
    for config in configs:
        model_name = config["name"]
        url = config["url"]
        
        print(f"   🤖 Zkouším: {model_name} ...")
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            # KDYŽ JE MODEL PŘETÍŽENÝ (Limit)
            if response.status_code == 429 or response.status_code == 403:
                print(f"   ⚠️ {model_name} je přetížen. Jdu na další...")
                time.sleep(1) 
                continue # Další v seznamu
            
            # KDYŽ MODEL NEEXISTUJE NEBO JINÁ CHYBA
            if response.status_code != 200:
                print(f"   Chyba {response.status_code} u {model_name}: {response.text}")
                continue # Další v seznamu

            # ÚSPĚCH
            result = response.json()
            if 'candidates' in result and result['candidates']:
                return result['candidates'][0]['content']['parts'][0]['text']
            
        except Exception as e:
            print(f"   Chyba spojení: {e}")
            
    return "Všechny modely selhaly (Google je dnes mimo provoz)."

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
    print("--- START BOTA (OPRAVENÝ HYBRID) ---")
    
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
                          f"Toto je složitá sázka. Napiš krátkou, chytrou predikci (1-2 věty).")
                icon = "🧠"
            else:
                prompt = (f"Trh: '{title}'. Šance na ANO je {price_txt}. "
                          f"Napiš k tomu jednu vtipnou glosu.")
                icon = "💰"

            # VOLÁNÍ OPRAVENÉ FUNKCE
            ai_text = ask_gemini_hybrid(prompt)
            print(f"   AI: {ai_text}")

            msg = f"{icon} *{title}*\n📊 Stav: {price_txt}\n💬 {ai_text}"
            send_tg(msg)
            
            print("   Odesláno. Pauza 20s...")
            time.sleep(20)

        except Exception as e:
            print(f"   Chyba: {e}")

if __name__ == "__main__":
    main()
