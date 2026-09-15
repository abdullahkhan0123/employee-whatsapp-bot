from flask import Flask, request
import sqlite3
import requests
import os
from google import genai

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

connection = sqlite3.connect("employees.db", check_same_thread=False)
cursor = connection.cursor()

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

def employee_info_with_ai(sawal):
    cursor.execute("SELECT name, department, salary FROM employees")
    all_employees = cursor.fetchall()

    employee_list = "\n".join(
        [f"{name}: department={dept}, salary={salary}" for name, dept, salary in all_employees]
    )

    prompt = f"""Tum ek HR assistant ho. Yeh humare employees ka data hai:
{employee_list}

User ka sawal: {sawal}

Is data ke basis par, user ke sawal ka Roman Urdu mein natural, friendly jawab do. Agar employee na mile to bata do. Jawab chota aur seedha rakho."""

    response = gemini_client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return response.text

def send_whatsapp_message(to_number, message_text):
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message_text}
    }
    response = requests.post(url, headers=headers, json=data)
    print("WhatsApp API Response:", response.status_code, response.text)

@app.route("/")
def home():
    return "Mera WhatsApp Bot Server Chal Raha Hai!"

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.get_json()
    try:
        entry = data["entry"][0]["changes"][0]["value"]
        message = entry["messages"][0]
        from_number = message["from"]
        text = message["text"]["body"]

        jawab = employee_info_with_ai(text)
        send_whatsapp_message(from_number, jawab)
    except (KeyError, IndexError):
        pass
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
