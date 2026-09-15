import sqlite3
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = "mera_secret_token_123"
ACCESS_TOKEN = "EAAPzqf56J8YBSWLGKLCSyBBUvRifZAqdpBVX6FhtKFYJpCgfeoQoknkmsnvD6Kx4gacykAuqcSXRyg2AGcKN83Gi9MbKGMD655FYSOrwr570xmEgzT1VYO5X2tAPLDBoaV3IhZAwoC3xh2uRPf9HAEbDZCvpHQGw459hNudGmN6xHWyRmsyZCzIAT9FcPdFfG4poGx57x0OEY1MRen5YLnzMbtB5y5s17jLQYHMgks1Xdlbyah8EE7HhUux90AZAVZBy94D9CfQnZByXhNYZBgJPek7v"
PHONE_NUMBER_ID = "1243326385539260"

connection = sqlite3.connect("employees.db", check_same_thread=False)
cursor = connection.cursor()

def employee_info(sawal):
    sawal = sawal.lower()
    cursor.execute("SELECT name, department, salary FROM employees")
    all_employees = cursor.fetchall()
    for emp in all_employees:
        emp_naam, emp_dept, emp_salary = emp
        if emp_naam.lower() in sawal:
            return f"Department: {emp_dept}, Salary: {emp_salary}"
    return "Yeh employee hamare paas nahi hai."

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

        jawab = employee_info(text)
        send_whatsapp_message(from_number, jawab)
    except (KeyError, IndexError):
        pass
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
