import os
from flask import Flask, request
from openai import OpenAI

app = Flask(__name__)

# Pegando a chave da OpenAI da variável de ambiente
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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
- Nunca inventar condutas fora da tabela base.
- Triagem passo a passo com opções numeradas (1, 2, 3).
- Em sintomas respiratórios, lembrar da ausculta de sibilos.
- Se algo não constar na tabela, responda: “❗Não consta no protocolo.”
- Uso educacional/simulado, não substitui julgamento médico.
"""

@app.route("/", methods=["POST"])
def safescan():
    data = request.get_json()
    user_text = data.get("message", "")

    completion = client.chat.completions.create(
        model="gpt-4o-mini",  # pode trocar para "gpt-5-mini" se quiser
        messages=[
            {"role": "system", "content": SAFESCAN_SYSTEM},
            {"role": "user", "content": user_text}
        ],
        temperature=0.2,
    )

    reply = completion.choices[0].message.content
    return {"reply": reply}

@app.route("/", methods=["GET"])
def healthcheck():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
