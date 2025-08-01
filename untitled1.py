import requests
import sqlite3
import time

TOKEN = "8481292967:AAFScdhliNb275incCE6_32eUYEG6u1D6Ec"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)""")
conn.commit()

user_state = {}

def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates?timeout=100"
    if offset:
        url += f"&offset={offset}"
    return requests.get(url).json()

def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def main():
    print("Bot Started...")
    last_update_id = None

    while True:
        updates = get_updates(last_update_id)
        if "result" in updates:
            for update in updates["result"]:
                last_update_id = update["update_id"] + 1
                if "message" in update:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"].get("text", "")

                    if chat_id in user_state:
                        state = user_state[chat_id]
                        if state["step"] == "signup_username":
                            state["username"] = text
                            send_message(chat_id, "Enter a password:")
                            state["step"] = "signup_password"

                        elif state["step"] == "signup_password":
                            password = text
                            try:
                                cursor.execute("INSERT INTO users(username, password) VALUES (?, ?)",
                                               (state["username"], password))
                                conn.commit()
                                send_message(chat_id, "✅ Sign Up Successful!")
                            except:
                                send_message(chat_id, "⚠️ Username already taken!")
                            user_state.pop(chat_id)

                        elif state["step"] == "signin_username":
                            state["username"] = text
                            send_message(chat_id, "Enter password:")
                            state["step"] = "signin_password"

                        elif state["step"] == "signin_password":
                            password = text
                            cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                                           (state["username"], password))
                            user = cursor.fetchone()
                            if user:
                                send_message(chat_id, "✅ Login Successful!")
                            else:
                                send_message(chat_id, "❌ Invalid username or password.")
                            user_state.pop(chat_id)

                    elif text == "/start":
                        send_message(chat_id, "👋 Welcome!\nChoose:\n1️⃣ /signup\n2️⃣ /signin")

                    elif text == "/signup":
                        send_message(chat_id, "Enter a username:")
                        user_state[chat_id] = {"step": "signup_username"}

                    elif text == "/signin":
                        send_message(chat_id, "Enter your username:")
                        user_state[chat_id] = {"step": "signin_username"}

        time.sleep(1)

if __name__ == "__main__":
    main()