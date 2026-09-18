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

    lang_instruction = "Respond only in English." if language == "en" else "Sirf Roman Urdu (Latin/English letters mein likhi hui Urdu) mein jawab do, Devanagari script ya Hindi lafz bilkul use mat karo."

    prompt = "Tum 'NCAI HR Assistant' ho, National Center of Artificial Intelligence ka official HR chatbot. " + lang_instruction + " Agar user apni marzi se dusri language mein likhe (English ya Roman Urdu), to usi language mein jawab do jisme user ne likha hai. ZAROORI: Sirf wahi maloomat do jo user ne poocha hai, aur kuch nahi. Agar user sirf poochhe 'kya [naam] hai' ya 'kya [naam] mojood hai', to sirf 'Haan, [naam] hamare paas mojood hain' jaisa chota jawab do - salary ya department mat batao jab tak specifically na poocha jaye. Agar user salary poochhe, sirf salary batao. Agar department poochhe, sirf department batao. Agar user 'sab kuch batao' ya 'poori detail do' kahe, tabhi poori maloomat do. Agar user general baat kare jaise 'theek hai', 'shukriya', to sirf chota polite jawab do, 'employee nahi mila' mat bolo aisi situation mein. Jawab hamesha 1-2 lines mein, seedha aur professional rakho, koi emoji nahi.\n\nEmployees ka data:\n" + employee_list + "\n\nUser ka message: " + sawal"

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
            "body": {"text": "Welcome to NCAI HR Assistant.\nHow can I help you today?\n\nPlease select your preferred language:"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "lang_en", "title": "English"}},
                    {"type": "reply", "reply": {"id": "lang_ur", "title": "Roman Urdu"}}
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
                send_whatsapp_message(from_number, "Roman Urdu set ho gayi hai. Mein aapki kya madad kar sakta hoon?")
            return "OK", 200

        text = message["text"]["body"]
        text_lower = text.lower().strip()

        if text_lower in ["hi", "hello", "menu", "start", "salam", "assalam o alaikum"]:
            send_language_buttons(from_number)
            return "OK", 200

        current_language = get_user_language(from_number)

        if current_language is None:
            send_language_buttons(from_number)
        else:
            jawab = employee_info_with_ai(text, current_language)
            send_whatsapp_message(from_number, jawab)

    except (KeyError, IndexError):
        pass
    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
