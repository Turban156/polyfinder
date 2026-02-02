import os
import requests
import google.generativeai as genai

# Konfigurace z GitHub Secrets
GEMINI_KEY = os.getenv(AIzaSyBaQdL5uqhG8AbSajErQSee761ronWrH9w)
TG_TOKEN = os.getenv(8044397219:AAEB09UfkqpneRYTROPYXxS89xWHnl4ImR8)
TG_CHAT_ID = os.getenv(5612770761)

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_polymarket_data():
    # Získáme top trhy (zjednodušeno přes veřejné API)
    url = "https://clob.polymarket.com/sampling-simplified-markets"
    try:
        resp = requests.get(url)
        return resp.json()[:10] # Sledujeme prvních 10 nejzajímavějších
    except:
        return []

def send_tg(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message})

def main():
    markets = get_polymarket_data()
    for m in markets:
        question = m.get('question', 'Neznámý trh')
        price = m.get('price', 0.5)
        
        # Analýza pomocí Gemini
        prompt = f"Trh: {question}. Aktuální cena 'ANO' je {price}. Je to s ohledem na aktuální rok 2026 a globální situaci zajímavá příležitost? Pokud ano, napiš stručně proč a začni slovem 'TIP'. Pokud ne, napiš 'NIC'."
        
        response = model.generate_content(prompt)
        ai_opinion = response.text.strip()
        
        if "TIP" in ai_opinion.upper():
            msg = f"🚀 {question}\nCena: {price}\nAnalýza: {ai_opinion}"
            send_tg(msg)

if __name__ == "__main__":
    main()
