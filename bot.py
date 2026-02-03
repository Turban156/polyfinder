import os
import requests
import json
import time

# Načtení klíčů
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Model, který víme, že funguje
MODEL_NAME = "models/gemini-2.5-flash"

def send_tg(message):
    if not TG_TOKEN or not TG_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message})
    except Exception as e:
        print(f"Chyba Telegramu: {e}")

def ask_gemini(prompt):
    if not GEMINI_KEY:
        return "Chybí klíč."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/{MODEL_NAME}:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        # Pokud jsme narazili na limit, vrátíme text, ale nezhroutíme se
        if response.status_code == 429 or response.status_code == 403:
            return "Limit vyčerpán (příště počkám déle)."
            
        if response.status_code != 200:
            return f"Chyba AI {response.status_code}"
            
        result = response.json()
        if 'candidates' in result and result['candidates']:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return "AI mlčí."
    except Exception as e:
        return f"Chyba spojení: {e}"

def get_gamma_data():
    print("Stahuji data...")
    url = "https://gamma-api.polymarket.com/events?limit=5&active=true&closed=false&sort=volume"
    try:
        resp = requests.get(url, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"Chyba stahování: {e}")
        return []

def main():
    print("--- START BOTA (30s PAUZA) ---")
    
    events = get_gamma_data()
    print(f"Staženo {len(events)} událostí.")

    if not events:
        print("Žádná data.")
        return

    # Zpracujeme 3 události
    for i, event in enumerate(events[:3]):
        try:
            title = event.get('title', 'Bez názvu')
            
            # --- VYLEPŠENÉ ČTENÍ CENY ---
            markets = event.get('markets', [])
            price_txt = "Viz Polymarket" # Výchozí text
            
            if markets:
                raw = markets[0].get('outcomePrices')
                # Zkusíme zjistit, jestli je to číslo nebo rozsah
                try:
                    if isinstance(raw, str): raw = json.loads(raw)
                    if isinstance(raw, list) and len(raw) > 0:
                        val = float(raw[0])
                        # Pokud je cena 0 nebo 1 přesně, je to divné -> asi složitý trh
                        if val > 0.01 and val < 0.99:
                            price_txt = f"{int(val*100)} %"
                        else:
                            price_txt = "Složitý trh"
                except:
                    price_txt = "Neznámá"

            print(f"[{i+1}] {title} (Cena: {price_txt})")

            # Dotaz na AI
            prompt = (f"Jsi vtipný glosátor. Trh: '{title}'. "
                      f"Napiš k tomu jednu krátkou, údernou, vtipnou větu česky.")
            
            ai_text = ask_gemini(prompt)
            print(f"   AI: {ai_text}")

            # Odeslání
            msg = f"🔔 *{title}*\n💰 Šance: {price_txt}\n💬 {ai_text}"
            send_tg(msg)
            
            # DŮLEŽITÉ: Dlouhá pauza 30 sekund
            print("   Dávám si kafíčko (30s pauza)...")
            time.sleep(30)

        except Exception as e:
            print(f"   Chyba: {e}")

if __name__ == "__main__":
    main()
