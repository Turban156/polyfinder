import os
import requests
import json
import time

# Načtení klíčů
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MODEL_NAME = "models/gemini-2.5-flash"

def send_tg(message):
    if not TG_TOKEN or not TG_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message})
    except Exception as e:
        print(f"Chyba Telegramu: {e}")

# TOTO JE TA HLAVNÍ ZMĚNA - Funkce, která se nevzdává
def ask_gemini_with_retry(prompt):
    if not GEMINI_KEY: return "Chybí klíč."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/{MODEL_NAME}:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    # Zkusíme to až 3x
    for attempt in range(3):
        try:
            print(f"   Volám AI (pokus {attempt+1}/3)...")
            response = requests.post(url, headers=headers, json=data)
            
            # KDYŽ NÁS GOOGLE STOPNE (Chyba 429)
            if response.status_code == 429 or response.status_code == 403:
                print("   ⚠️ NARAZIL JSEM NA LIMIT. Čekám 65 sekund a zkusím to znova...")
                time.sleep(65) # Počkáme minutu a kousek
                continue # A jedeme znova smyčku
                
            if response.status_code != 200:
                return f"Chyba AI {response.status_code}"
            
            # KDYŽ TO KLAPNE
            result = response.json()
            if 'candidates' in result and result['candidates']:
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                return "AI nemá názor."
                
        except Exception as e:
            return f"Chyba spojení: {e}"
            
    return "Bohužel, Google je dnes přetížený (ani po 3 pokusech to nešlo)."

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
    print("--- START BOTA (AUTO-RETRY VERZE) ---")
    
    # Bezpečnostní pauza na začátku, kdybyste to spustil moc brzy po sobě
    print("Zahřívací pauza 10s...")
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

            # Výběr promptu
            if is_complex:
                prompt = (f"Jsi zkušený analytik. Trh: '{title}'. "
                          f"Toto je složitá sázka. Napiš krátkou, vtipnou predikci, jak to dopadne. "
                          f"Max 2 věty.")
                icon = "🧠"
            else:
                prompt = (f"Trh: '{title}'. Šance na ANO je {price_txt}. "
                          f"Napiš k tomu jednu vtipnou glosu.")
                icon = "💰"

            # TADY VOLÁME NOVOU FUNKCI S OPAKOVÁNÍM
            ai_text = ask_gemini_with_retry(prompt)
            print(f"   AI: {ai_text}")

            msg = f"{icon} *{title}*\n📊 Stav: {price_txt}\n💬 {ai_text}"
            send_tg(msg)
            
            # I když to prošlo, dáme si pauzu pro jistotu
            print("   Úspěch. Pauza 20s před dalším...")
            time.sleep(20)

        except Exception as e:
            print(f"   Chyba: {e}")

if __name__ == "__main__":
    main()
