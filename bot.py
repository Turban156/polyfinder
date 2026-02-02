import os
import requests
import google.generativeai as genai

# TADY NIC NEMĚŇ - kód si klíče sám vytáhne z GitHubu
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_polymarket_data():
    url = "https://clob.polymarket.com/sampling-simplified-markets"
    try:
        resp = requests.get(url)
        return resp.json()[:10]
    except Exception as e:
        print(f"Chyba při načítání dat: {e}")
        return []

def send_tg(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message})

def main():
    markets = get_polymarket_data()
    if not markets:
        return

    for m in markets:
        question = m.get('question', 'Neznámý trh')
        price = m.get('price', 0.5)
        
        prompt = f"Trh: {question}. Aktuální cena 'ANO' je {price}. Je to s ohledem na aktuální rok 2026 zajímavá příležitost? Pokud ano, napiš stručně proč a začni slovem 'TIP'. Pokud ne, napiš 'NIC'."
        
        try:
            response = model.generate_content(prompt)
            ai_opinion = response.text.strip()
            
            if "TIP" in ai_opinion.upper():
                msg = f"🚀 {question}\nCena: {price}\nAnalýza: {ai_opinion}"
                send_tg(msg)
                print(f"Odeslán tip na: {question}")
        except Exception as e:
            print(f"Chyba u Gemini: {e}")

if __name__ == "__main__":
    main()
