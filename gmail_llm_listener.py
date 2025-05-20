import os
import json
import base64
import re
import time

from openai import OpenAI
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def ask_llm(subject, body):
    prompt = f"""
Na podstawie poniższego maila wyodrębnij dane w dokładnie takim formacie JSON jak poniżej.
Wypełnij wszystkie pola, nawet jeśli trzeba je oszacować z treści. Używaj podwójnych cudzysłowów i nie dodawaj nic poza JSON-em.

Format wzorcowy:
{{
  "typ_zgłoszenia": "problem z fakturą",
  "data_faktury": "2023-04-14",
  "numer_faktury": "FA/04/238",
  "opis_problemu": "...",
  "klient": {{
    "imię_i_nazwisko": "...",
    "firma": "...",
    "numer_telefonu": "..."
  }},
  "akcja_oczekiwana": "..."
}}

Temat: {subject}

Treść:
\"\"\"
{body}
\"\"\"
"""

    try:
        response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()

        # Usuń ewentualny markdown ```json ... ```
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            print("❌ Nie udało się znaleźć poprawnego bloku JSON")
    except Exception as e:
        print("❌ Błąd LLM:", e)
    return {}


def append_to_json_file(data, filename="output.json"):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
    else:
        existing = []

    existing.append(data)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

def get_gmail_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def get_latest_messages(service, processed_ids, start_time):
    results = service.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=10).execute()
    messages = results.get("messages", [])
    new_msgs = []

    for msg in messages:
        msg_id = msg["id"]
        if msg_id in processed_ids:
            continue

        msg_data = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
        internal_date = int(msg_data.get("internalDate", 0))

        # ✅ tylko nowe wiadomości po uruchomieniu
        if internal_date <= start_time:
            continue

        headers = msg_data["payload"]["headers"]
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        body = ""
        parts = msg_data["payload"].get("parts", [])
        if parts:
            for part in parts:
                if part["mimeType"] == "text/plain":
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                    break
        else:
            body = base64.urlsafe_b64decode(msg_data["payload"]["body"]["data"]).decode("utf-8")

        new_msgs.append((msg_id, subject, body))
    return new_msgs

def main():
    service = get_gmail_service()
    processed_ids = set()
    start_time = int(time.time() * 1000)  # czas w milisekundach
    print("📬 Oczekiwanie na nowe maile (tylko po starcie skryptu)...")

    while True:
        new_messages = get_latest_messages(service, processed_ids, start_time)
        for msg_id, subject, body in new_messages:
            print(f"📨 Nowy mail: {subject}")
            data = ask_llm(subject, body)
            if data:
                append_to_json_file(data)
                print("✅ Zapisano do output.json")
            processed_ids.add(msg_id)
        time.sleep(60)

if __name__ == "__main__":
    main()

