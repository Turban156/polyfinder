import os
import requests
import google.generativeai as genai

# Tady říkáme botovi: "Podívej se do GitHub Secrets pod tímto názvem"
# NEVKLÁDEJ SEM SVÉ KLÍČE PŘÍMO!
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Kontrola, jestli se klíče načetly (pro debug v logu)
if not GEMINI_KEY:
    print("CHYBA: Nenalezen GEMINI_API_KEY v Secrets!")
if not TG_TOKEN:
    print("CHYBA: Nenalezen TELEGRAM_TOKEN v Secrets!")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_polymarket_data():
    print("Stahuji data z Polymarketu...")
    url = "https://clob.polymarket.com/sampling-simplified-markets"
    try:
        resp = requests.get(url)
        data = resp.json()
        print(f"Staženo {len(data)} trhů.")
        return data[:10]
    except Exception as e:
        print(f"Chyba při stahování: {e}")
        return []

def send_tg(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    response = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message})
    if response.status_code != 200:
        print(f"Chyba odeslání na Telegram: {response.text}")

def main():
    markets = get_polymarket_data()
    for m in markets:
        question = m.get('question', 'Neznámý trh')
        price = m.get('price', 0.5) # Zkusíme jiný klíč pro cenu, API se mění
        
        # Ochrana proti chybějící ceně
        if price is None: 
            price = "Neznámá"

        prompt = f"Trh: {question}. Cena za 'ANO': {price}. Je to v roce 2026 zajímavá příležitost? Pokud ano, začni slovem TIP."
        
        try:
            response = model.generate_content(prompt)
            ai_opinion = response.text.strip()
            # Pro testování vypíšeme vše do logu
            print(f"Analýza {question}: {ai_opinion[:50]}...") 
            
            if "TIP" in ai_opinion.upper():
                msg = f"🚀 {question}\nCena: {price}\n{ai_opinion}"
                send_tg(msg)
        except Exception as e:
            print(f"Chyba AI: {e}")

if __name__ == "__main__":
    main()
