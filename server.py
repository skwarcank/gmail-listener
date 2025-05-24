import time
import json
import os
import traceback
from GmailService import GmailService
from AIService import AIService
from DBService import DBService
from langfuse import Langfuse

def append_to_json_file(data, filename="output.json"):
    # Dodaje nowe dane do pliku JSON (tworzy plik jeśli nie istnieje)
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
    # Inicjalizacja klienta Langfuse do śledzenia trace'ów
    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST"),
    )
    # Inicjalizacja serwisów do obsługi maili, AI i bazy danych
    gmail_service = GmailService()
    ai_service = AIService()
    db_service = DBService()
    processed_ids = set()  # Zbiór przetworzonych ID maili, by nie przetwarzać ich ponownie
    start_time = int(time.time() * 1000)  # Czas startu (do filtrowania maili)
    print("📬 Oczekiwanie na nowe maile (tylko po starcie skryptu)...")

    while True:
        try:
            # Pobierz nowe wiadomości z Gmaila
            new_messages = gmail_service.get_latest_messages(processed_ids, start_time)
            for msg_id, subject, body in new_messages:
                # Utwórz trace w Langfuse dla przetwarzania jednego maila
                trace = langfuse.trace(
                    name="mail_processing",
                    user_id="mailbot"
                )

                # Zarejestruj krok odebrania maila w trace
                langfuse.span(
                    name="mail_received",
                    input={"subject": subject, "body": body},
                    trace_id=trace.id,
                    parent_id=None
                )

                print(f"📨 Nowy mail: {subject}")
                try:
                    # Krok: przetwarzanie maila przez LLM
                    data = ai_service.ask_llm(subject, body, trace)

                    # Zarejestruj odpowiedź LLM jako krok w trace
                    langfuse.span(
                        name="llm_response",
                        output=data,
                        trace_id=trace.id,
                        parent_id=None
                    )

                    if data:
                        # Zapisz dane do pliku JSON
                        append_to_json_file(data)
                        print("✅ Zapisano do output.json")
                        # Zapisz dane do bazy (np. Airtable)
                        db_service.insert_row(data)

                        # Zarejestruj krok zapisu do bazy w trace
                        langfuse.span(
                            name="db_insert",
                            output="OK",
                            trace_id=trace.id,
                            parent_id=None
                        )
                except Exception as e:
                    # Obsługa błędów związanych z AIService lub LLM
                    print(f"❌ Błąd AIService: {e}")
                    traceback.print_exc()
                # Dodaj ID maila do przetworzonych, by nie przetwarzać go ponownie
                processed_ids.add(msg_id)
        except Exception as e:
            # Obsługa błędów związanych z pobieraniem maili lub innymi operacjami
            print(f"❌ Błąd GmailService: {e}")
            traceback.print_exc()
        # Odczekaj 10 sekund przed kolejnym sprawdzeniem skrzynki
        time.sleep(10)

if __name__ == "__main__":
    main()




