import os
import threading
from flask import Flask, request, jsonify
from openai import OpenAI

# --- Flask (mantém a Render feliz e permite teste via POST) ---
app = Flask(__name__)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")  # defina na Render

SAFESCAN_SYSTEM = """Você é o SafeScan, um assistente de protocolos de intercorrências
para exames de TC/RM. Responda SEMPRE no formato WhatsApp, curto, objetivo e
exclusivamente com base na TABELA BASE fornecida pelo serviço (nada fora dela).

Formato fixo:
Intercorrência
📊 Monitorização
🛏️ Medidas imediatas
💊 Medicação (dose e via) — apenas se constar na tabela
⏱️ Tempo de monitoramento
🧭 Orientação
⚠️ Observações

Regras críticas:
- Nunca inventar condutas fora da TABELA BASE.
- Triagem passo a passo com opções numeradas (1, 2, 3…).
- Em sintomas respiratórios, lembrar da ausculta de sibilos.
- Se algo não constar na tabela, responda: “❗Não consta no protocolo.”
- Uso educacional/simulado; não substitui julgamento médico.
"""

def safescan_reply(user_text: str) -> str:
    comp = client.chat.completions.create(
        model="gpt-4o-mini",   # pode trocar para "gpt-5-mini" se preferir
        temperature=0.2,
        messages=[
            {"role": "system", "content": SAFESCAN_SYSTEM},
            {"role": "user", "content": user_text},
        ],
    )
    return comp.choices[0].message.content

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/", methods=["POST"])
def http_api():
    data = request.get_json(silent=True) or {}
    msg = data.get("message", "")
    return jsonify({"reply": safescan_reply(msg)})

# --- Telegram (polling em thread separada) ---
def start_telegram_bot():
    # somente inicia se o token existir
    if not TELEGRAM_TOKEN:
        print("TELEGRAM_TOKEN não definido. Bot do Telegram não iniciado.")
        return

    from telegram.ext import Updater, MessageHandler, Filters

    def on_message(update, context):
        text = update.message.text or ""
        try:
            reply = safescan_reply(text)
        except Exception as e:
            reply = "Houve um erro temporário. Tente novamente em instantes."
            print(f"Erro OpenAI: {e}")
        update.message.reply_text(reply, disable_web_page_preview=True)

    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, on_message))
    updater.start_polling()
    print("Bot do Telegram em execução (polling).")
    updater.idle()

def run():
    # inicia Telegram em paralelo, mantendo o web service do Flask
    t = threading.Thread(target=start_telegram_bot, daemon=True)
    t.start()
    # Render espera um servidor web ouvindo na porta
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    run()
