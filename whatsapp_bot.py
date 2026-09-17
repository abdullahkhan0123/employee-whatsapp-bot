from flask import Flask, request
import sqlite3
import requests
import os
from google import genai

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "").strip()
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "").strip()
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

connection = sqlite3.connect("employees.db", check_same_thread=False)
cursor = connection.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS user_preferences (phone_number TEXT PRIMARY KEY, language TEXT)")
connection.commit()

gemini_client = genai.Client(api_key=GEMINI_API_KEY)


def get_user_language(phone_number):
    cursor.execute("SELECT language FROM user_preferences WHERE phone_number = ?", (phone_number,))
    row = cursor.fetchone()
    return row[0] if row else None


def set_user_language(phone_number, language):
    cursor.execute("INSERT OR REPLACE INTO user_preferences (phone_number, language) VALUES (?, ?)", (phone_number, language))
    connection.commit()


def employee_info_with_ai(sawal, language):
    cursor.execute("SELECT name, department, salary FROM employees")
    all_employees = cursor.fetchall()
    employee_list = "\n".join([f"{name}: department={dept}, salary={salary}" for name, dept, salary in all_employees])

    lang_instruction = "Respond in English." if language == "en" else "Roman Urdu mein jawab do."

    prompt = "Tum 'NCIA HR Assistant' ho, National Center of Artificial Intelligence ka official HR chatbot. Sirf employee ki maloomat (naam, department, salary) do, sirf jo poocha jaye wahi batao. Kisi general topic par baat mat karo. Jawab hamesha 1-2 lines mein, seedha aur professional rakho, koi emoji nahi. " + lang_instruction + " Agar user jis language mein likhe usi mein jawab do, chahe unhone pehle koi aur language select ki ho.\n\nEmployees ka data:\n" + employee_list + "\n\nUser ka message: " + sawal

    response = gemini_client.models.generate_content(model="gemini-3.5-flash-lite", contents=prompt)
    return response.text


def send_whatsapp_message(to_number, message_text):
    url = "https://graph.facebook.com/v21.0/" + PHONE_NUMBER_ID + "/messages"
    headers = {"Authorization": "Bearer " + ACCESS_TOKEN, "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": to_number, "type": "text", "text": {"body": message_text}}
    response = requests.post(url, headers=headers, json=data)
    print("WhatsApp API Response:", response.status_code, response.text)


def send_language_buttons(to_number):
    url = "https://graph.facebook.com/v21.0/" + PHONE_NUMBER_ID + "/messages"
    headers = {"Authorization": "Bearer " + ACCESS_TOKEN, "Content-Type": "application/json"}
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "Welcome to NCIA HR Assistant.\nNCIA HR Assistant mein khush aamdeed.\n\nPlease select your language / Zaban select karein:"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "lang_en", "title": "English"}},
                    {"type": "reply", "reply": {"id": "lang_ur", "title": "Urdu"}}
                ]
            }
        }
    }
    response = requests.post(url, headers=headers, json=data)
    print("Button Message Response:", response.status_code, response.text)


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

        if message["type"] == "interactive":
            button_id = message["interactive"]["button_reply"]["id"]
            if button_id == "lang_en":
                set_user_language(from_number, "en")
                send_whatsapp_message(from_number, "Language set to English. How can I help you?")
            elif button_id == "lang_ur":
                set_user_language(from_number, "ur")
                send_whatsapp_message(from_number, "Zaban Urdu set ho gayi hai. Mein aapki kya madad kar sakta hoon?")
            return "OK", 200

        text = message["text"]["body"]
        current_language = get_user_language(from_number)

        if current_language is None:
            send_language_buttons(from_number)
            set_user_language(from_number, "en")
        else:
            jawab = employee_info_with_ai(text, current_language)
            send_whatsapp_message(from_number, jawab)

    except (KeyError, IndexError):
        pass
    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
