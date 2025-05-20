import time
import json
import os
from GmailService import get_gmail_service, get_latest_messages
from AIService import ask_llm

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

def main():
    service = get_gmail_service()
    processed_ids = set()
    start_time = int(time.time() * 1000)
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


