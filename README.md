NCAI HR Assistant:

An AI-powered WhatsApp chatbot that provides employee information for the National Center of Artificial Intelligence (NCAI). Built as a learning project to explore the full stack of building, deploying, and scaling a production-style chatbot — from a simple rule-based script to a cloud-hosted, AI-powered assistant.

Features:

- WhatsApp Integration — Chat directly through WhatsApp using the Meta WhatsApp Business API
- Bilingual Support — Responds in English or Roman Urdu, selectable via interactive buttons
- AI-Powered Understanding — Uses Google Gemini to understand natural language queries, not just fixed keywords
- SQLite Database — Stores employee records (name, department, salary) and user language preferences
- Live 24/7 — Hosted on Railway with automatic deployment from GitHub
- Secure — API keys and tokens stored as environment variables, never hardcoded

How It Works:

User sends WhatsApp message → Meta WhatsApp API forwards it to the webhook → Flask server receives the message → New user? Send language selection buttons (English / Roman Urdu) → Returning user? Query employee database + send to Gemini AI → Gemini generates a natural, professional reply in the chosen language → Reply sent back to the user via WhatsApp

Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Web Framework | Flask |
| Database | SQLite |
| AI / LLM | Google Gemini API |
| Messaging | Meta WhatsApp Business API |
| Hosting | Railway |
| Version Control | GitHub |

 Project Structure:

- whatsapp_bot.py — Main Flask app: webhook, AI logic, WhatsApp messaging
- employees.db — SQLite database with employee records
- requirements.txt — Python dependencies
- Procfile — Tells Railway how to start the app

Environment Variables:

This project keeps all secrets out of the codebase. The following variables must be set in the hosting environment (e.g. Railway → Variables tab):

| Variable | Description |
|---|---|
| VERIFY_TOKEN | Custom token used to verify the Meta webhook |
| ACCESS_TOKEN | Permanent WhatsApp Business API access token |
| PHONE_NUMBER_ID | WhatsApp Business phone number ID |
| GEMINI_API_KEY | Google Gemini API key |

 What I Learned Building This:

- Structuring data with SQL and dictionaries
- Building and deploying a Flask web server
- Integrating third-party APIs (Meta WhatsApp, Google Gemini)
- Debugging real production issues: crashes, token expiry, whitespace bugs, webhook subscriptions
- Prompt engineering to control an LLM's tone, language, and behavior
- Cloud deployment and environment variable security best practices

Author:

Built by Abdullah as a hands-on project to learn the fundamentals before moving toward agentic AI systems.
