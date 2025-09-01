import os
from telegram.ext import Updater, MessageHandler, Filters
from openai import OpenAI

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

client = OpenAI(api_key=OPENAI_API_KEY)

SAFESCAN_SYSTEM = """Você é o SafeScan...
(cole aqui as regras que já definimos)
"""

def responder(update, context):
    texto = update.message.text
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SAFESCAN_SYSTEM},
            {"role": "user", "content": texto}
        ],
        temperature=0.2,
    )
    resposta = completion.choices[0].message.content
    update.message.reply_text(resposta)

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, responder))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
