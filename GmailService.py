import os
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailService:
    def __init__(self, token_file="token.json", credentials_file="credentials.json"):
        # Inicjalizacja ścieżek do plików tokenów i poświadczeń
        self.token_file = token_file
        self.credentials_file = credentials_file
        # Utworzenie klienta Gmail API
        self.service = self._get_gmail_service()

    def _get_gmail_service(self):
        # Autoryzacja użytkownika i utworzenie obiektu klienta Gmail API
        creds = None
        if os.path.exists(self.token_file):
            # Jeśli istnieje plik tokena, użyj go do autoryzacji
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        else:
            # Jeśli nie ma tokena, przeprowadź proces autoryzacji i zapisz token
            flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())
        # Zwróć klienta Gmail API
        return build("gmail", "v1", credentials=creds)

    def get_latest_messages(self, processed_ids, start_time):
        # Pobiera najnowsze wiadomości z Gmaila, pomijając już przetworzone i starsze niż start_time
        results = self.service.users().messages().list(
            userId="me", labelIds=["INBOX"], maxResults=10
        ).execute()
        messages = results.get("messages", [])
        new_msgs = []

        for msg in messages:
            msg_id = msg["id"]
            # Pomija wiadomości, które już zostały przetworzone
            if msg_id in processed_ids:
                continue

            # Pobiera pełne dane wiadomości
            msg_data = self.service.users().messages().get(
                userId="me", id=msg_id, format="full"
            ).execute()
            internal_date = int(msg_data.get("internalDate", 0))

            # Pomija wiadomości starsze niż start_time
            if internal_date <= start_time:
                continue

            # Pobiera temat wiadomości z nagłówków
            headers = msg_data["payload"]["headers"]
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
            body = ""
            # Obsługuje wiadomości wieloczęściowe (multipart)
            parts = msg_data["payload"].get("parts", [])
            if parts:
                for part in parts:
                    if part["mimeType"] == "text/plain":
                        # Dekoduje treść tekstową wiadomości
                        body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                        break
            else:
                # Jeśli nie ma części, pobiera treść z głównego body
                body = base64.urlsafe_b64decode(msg_data["payload"]["body"]["data"]).decode("utf-8")

            # Dodaje nową wiadomość do listy wynikowej
            new_msgs.append((msg_id, subject, body))
        return new_msgs
