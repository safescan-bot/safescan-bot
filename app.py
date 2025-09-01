import os
import threading
from flask import Flask, request, jsonify
from openai import OpenAI

# ------------------- Configuração -------------------
app = Flask(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")          # defina na Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")          # defina na Render
PORT = int(os.environ.get("PORT", 10000))                  # Render usa PORT

client = OpenAI(api_key=OPENAI_API_KEY)

SAFESCAN_SYSTEM = """Você é o SafeScan, um assistente de protocolos de intercorrências
para exames de TC/RM. Responda SEMPRE no formato WhatsApp, curto, objetivo e
EXCLUSIVAMENTE com base na TABELA BASE fornecida pela clínica (nada fora dela).

Formato fixo:
Intercorrência
📊 Monitorização
🛏️ Medidas imediatas
💊 Medicação (dose e via) — apenas se constar na TABELA BASE
⏱️ Tempo de monitoramento
🧭 Orientação
⚠️ Observações

Regras críticas:
- Nunca sugerir condutas fora da TABELA BASE (se pedirem: “❗Não consta no protocolo.”).
- Triagem passo a passo com opções numeradas (1, 2, 3…).
- Em sintomas respiratórios, orientar AUSCULTA para avaliar sibilos antes da conduta.
- Uso educacional/simulado; não substitui julgamento médico.
"""

# ------------------- Núcleo SafeScan -------------------
def safescan_reply(user_text: str) -> str:
    if not OPENAI_API_KEY:
        return "Chave da OpenAI ausente. Configure OPENAI_API_KEY na Render."
    try:
        comp = client.chat.completions.create(
            model="gpt-4o-mini",      # troque para "gpt-5-mini" se preferir
            temperature=0.2,
            messages=[
                {"role": "system", "content": SAFESCAN_SYSTEM},
                {"role": "user", "content": user_text},
            ],
        )
        return comp.choices[0].message.content
    except Exception as e:
        print(f"[SafeScan][Erro OpenAI] {e}")
        return "Houve um erro temporário ao consultar o modelo. Tente novamente."

# ------------------- API HTTP (para testes) -------------------
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/", methods=["POST"])
def http_api():
    data = request.get_json(silent=True) or {}
    msg = (data.get("message") or "").strip()
    if not msg:
        return jsonify({"error": "Campo 'message' vazio."}), 400
    return jsonify({"reply": safescan_reply(msg)})

# ------------------- Telegram (polling) -------------------
def start_telegram_bot():
    if not TELEGRAM_TOKEN:
        print("[Telegram] TELEGRAM_TOKEN não definido. Bot não iniciado.")
        return
    try:
        from telegram.ext import Updater, MessageHandler, Filters, CommandHandler

        def on_start(update, context):
            update.message.reply_text(
                "SafeScan pronto. Envie o sintoma em linguagem natural.\n"
                "Ex.: 'coceira no pescoço e náuseas'"
            )

        def on_message(update, context):
            text = update.message.text or ""
            reply = safescan_reply(text)
            update.message.reply_text(reply, disable_web_page_preview=True)

        updater = Updater(TELEGRAM_TOKEN, use_context=True)
        dp = updater.dispatcher
        dp.add_handler(CommandHandler("start", on_start))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, on_message))

        updater.start_polling()
        print("[Telegram] Bot em execução (polling).")
        updater.idle()
    except Exception as e:
        print(f"[Telegram][Erro] {e}")

def run():
    # Inicia o bot do Telegram em thread separada e mantém o servidor web
    t = threading.Thread(target=start_telegram_bot, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    run()
