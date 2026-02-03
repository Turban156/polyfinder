import os
import requests
import json
import time

# Načtení klíčů
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Model
MODEL_NAME = "models/gemini-2.5-flash"

def send_tg(message):
    if not TG_TOKEN or not TG_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message})
    except Exception as e:
        print(f"Chyba Telegramu: {e}")

def ask_gemini(prompt):
    if not GEMINI_KEY: return "Chybí klíč."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/{MODEL_NAME}:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 429 or response.status_code == 403:
            return "Limit vyčerpán (příště počkám déle)."
            
        if response.status_code != 200:
            return f"Chyba AI {response.status_code}"
            
        result = response.json()
        if 'candidates' in result and result['candidates']:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return "AI nemá názor."
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
    print("--- START BOTA (EXPERT ANALÝZA) ---")
    
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
            
            # Zjištění ceny
            if markets:
                raw = markets[0].get('outcomePrices')
                try:
                    if isinstance(raw, str): raw = json.loads(raw)
                    if isinstance(raw, list) and len(raw) > 0:
                        val = float(raw[0])
                        # Pokud je cena smysluplná (mezi 1% a 99%)
                        if val > 0.01 and val < 0.99:
                            price_txt = f"{int(val*100)} %"
                        else:
                            price_txt = "Složitý trh (více možností)"
                            is_complex = True
                except:
                    price_txt = "Neznámá"
                    is_complex = True

            print(f"[{i+1}] {title} (Cena: {price_txt})")

            # --- INTELIGENTNÍ VÝBĚR PROMPTU ---
            if is_complex:
                # Hloubková analýza bez znalosti přesné ceny
                prompt = (f"Jsi zkušený krypto/burzovní analytik. Trh: '{title}'. "
                          f"Toto je složitá sázka s mnoha možnostmi, takže neznám přesná procenta. "
                          f"Přesto mi napiš krátkou, chytrou a vtipnou analýzu o tom, jak to asi dopadne. "
                          f"Buď konkrétní (zmíni aktéry).")
                icon = "🧠" # Ikona pro analýzu
            else:
                # Klasická reakce na cenu
                prompt = (f"Trh: '{title}'. Šance na ANO je {price_txt}. "
                          f"Napiš k tomu jednu vtipnou větu.")
                icon = "💰"

            ai_text = ask_gemini(prompt)
            print(f"   AI: {ai_text}")

            # Odeslání
            msg = f"{icon} *{title}*\n📊 Stav: {price_txt}\n💬 {ai_text}"
            send_tg(msg)
            
            # Pauza 60 sekund je NUTNÁ, protože teď voláme AI pokaždé
            print("   Čekám 60 sekund (obnovení limitů)...")
            time.sleep(60)

        except Exception as e:
            print(f"   Chyba: {e}")

if __name__ == "__main__":
    main()
