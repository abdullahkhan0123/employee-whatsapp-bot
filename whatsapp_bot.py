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
