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

# 1. KROK: ZJISTIT, JAKÝ MODEL FUNGUJE
def get_best_model():
    if not GEMINI_KEY:
        print("Chybí API klíč!")
        return None

    print("🔍 Hledám dostupný AI model...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}"
    
    try:
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"Chyba při hledání modelů: {resp.text}")
            return "models/gemini-pro" # Fallback

        data = resp.json()
        # Projdeme seznam a najdeme první, co umí generovat text
        for m in data.get('models', []):
            name = m.get('name')
            methods = m.get('supportedGenerationMethods', [])
            if 'generateContent' in methods and 'gemini' in name:
                print(f"✅ Nalezen funkční model: {name}")
                return name
                
    except Exception as e:
        print(f"Chyba připojení k Google: {e}")
    
    return "models/gemini-1.5-flash" # Poslední záchrana

# Uložíme si název modelu do proměnné
CURRENT_MODEL = None 

def ask_gemini_auto(prompt):
    global CURRENT_MODEL
    if not CURRENT_MODEL:
        CURRENT_MODEL = get_best_model()
    
    if not CURRENT_MODEL:
        return "AI není k dispozici."

    # Voláme API s automaticky nalezeným modelem
    url = f"https://generativelanguage.googleapis.com/v1beta/{CURRENT_MODEL}:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            return f"Error {response.status_code}"
            
        result = response.json()
        if 'candidates' in result and result['candidates']:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return "Prázdná odpověď."
    except Exception as e:
        return f"Chyba: {e}"

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
    print("--- START BOTA (AUTO-DETECT) ---")
    
    # Nejdřív najdeme model (aby to nezdržovalo v cyklu)
    global CURRENT_MODEL
    CURRENT_MODEL = get_best_model()
    
    events = get_gamma_data()
    print(f"Staženo {len(events)} událostí.")

    if not events:
        print("Žádná data.")
        return

    for i, event in enumerate(events[:3]):
        try:
            title = event.get('title', 'Bez názvu')
            markets = event.get('markets', [])
            
            price_display = "Neznámá"
            
            if markets:
                # DEBUG: Vypíšeme surová data ceny, abychom viděli, proč je to 0.0
                raw = markets[0].get('outcomePrices')
                print(f"   DEBUG CENA pro '{title}': {raw}")
                
                try:
                    # Zkusíme to rozparsovat
                    if isinstance(raw, str): raw = json.loads(raw)
                    if isinstance(raw, list) and len(raw) > 0:
                        val = float(raw[0])
                        price_display = str(round(val, 2))
                except:
                    price_display = "Chyba čtení"

            print(f"[{i+1}] {title} (Cena: {price_display})")

            # Dotaz na AI
            prompt = (f"Jsi analytik. Trh: '{title}'. Cena ANO je {price_display}. "
                      f"Napiš k tomu 1 krátkou vtipnou větu.")
            
            ai_text = ask_gemini_auto(prompt)
            print(f"   AI: {ai_text}")

            # Odeslání
            msg = f"🤖 *{title}*\nCena: {price_display}\n💬 {ai_text}"
            send_tg(msg)
            
            time.sleep(3)

        except Exception as e:
            print(f"   Chyba: {e}")

if __name__ == "__main__":
    main()
