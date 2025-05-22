import time
import json
import os
import traceback
from GmailService import GmailService
from AIService import AIService

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
    gmail_service = GmailService()
    ai_service = AIService()
    processed_ids = set()
    start_time = int(time.time() * 1000)
    print("📬 Oczekiwanie na nowe maile (tylko po starcie skryptu)...")

    while True:
        try:
            new_messages = gmail_service.get_latest_messages(processed_ids, start_time)
            for msg_id, subject, body in new_messages:
                print(f"📨 Nowy mail: {subject}")
                try:
                    data = ai_service.ask_llm(subject, body)
                    if data:
                        append_to_json_file(data)
                        print("✅ Zapisano do output.json")
                except Exception as e:
                    print(f"❌ Błąd AIService: {e}")
                    traceback.print_exc()
                processed_ids.add(msg_id)
        except Exception as e:
            print(f"❌ Błąd GmailService: {e}")
            traceback.print_exc()
        time.sleep(60)

if __name__ == "__main__":
    main()


