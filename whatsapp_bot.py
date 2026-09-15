from flask import Flask, request
import os

app = Flask(__name__)

VERIFY_TOKEN = "mera_secret_token_123"

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
    else:
        return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.get_json()
    print("Naya message aaya:", data)
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)