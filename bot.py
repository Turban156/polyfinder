import os
import requests
import json
import time

# Načtení klíčů
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# POUŽIJEME VÁŠ OBJEVENÝ MODEL
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
        
        # Ošetření chyby 403 (Limity)
        if response.status_code == 429 or response.status_code == 403:
            return "Moc rychlé dotazy na AI (Limit)."
        if response.status_code != 200:
            return f"Chyba AI {response.status_code}"
            
        result = response.json()
        if 'candidates' in result and result['candidates']:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return "Mlčící AI."
    except Exception as e:
        return f"Chyba spojení: {e}"

def get_gamma_data():
    print("Stahuji data...")
    # Řadíme podle objemu, ať jsou to ty nejžhavější
    url = "https://gamma-api.polymarket.com/events?limit=5&active=true&closed=false&sort=volume"
    try:
        resp = requests.get(url, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"Chyba stahování: {e}")
        return []

def main():
    print(f"--- START BOTA ({MODEL_NAME}) ---")
    
    events = get_gamma_data()
    print(f"Staženo {len(events)} událostí.")

    if not events:
        print("Žádná data.")
        return

    # Projdeme první 3 události
    for i, event in enumerate(events[:3]):
        try:
            title = event.get('title', 'Bez názvu')
            
            # Zkusíme najít cenu, pokud je 0, napíšeme Info
            markets = event.get('markets', [])
            price_txt = "Neznámá"
            
            if markets:
                raw = markets[0].get('outcomePrices')
                # Pokud je to ["0", "1"], tak to není cena, ale rozsah
                if isinstance(raw, list) and len(raw) > 0:
                    if raw[0] == "0" or raw[0] == "0.0":
                        price_txt = "Viz Polymarket"
                    else:
                        price_txt = str(round(float(raw[0]), 2))
            
            print(f"[{i+1}] {title} (Cena: {price_txt})")

            # Dotaz na AI
            prompt = (f"Jsi vtipný glosátor trhu. Trh: '{title}'. "
                      f"Napiš k tomu jednu kousavou nebo vtipnou větu česky.")
            
            ai_text = ask_gemini(prompt)
            print(f"   AI: {ai_text}")

            # Odeslání
            msg = f"🔔 *{title}*\n💰 Cena: {price_txt}\n💬 {ai_text}"
            send_tg(msg)
            
            # DŮLEŽITÉ: Dlouhá pauza pro Free verzi modelu 2.5
            print("   Pauza 12 sekund (kvůli limitům Google)...")
            time.sleep(12)

        except Exception as e:
            print(f"   Chyba: {e}")

if __name__ == "__main__":
    main()
