import os
import base64
from google.oauth2.credentials import Credentials           #Dostęp do Google API
from google_auth_oauthlib.flow import InstalledAppFlow      #Proces autoryzacji
from googleapiclient.discovery import build                 #Interakcja z API

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']     #zakres dostępu(czytanie wiadomości)

def get_gmail_service():                #uzyskanie dostępu do Gmail API
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)        #inicjuje proces autoryzacji
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)      #zwraca obiekt usługi Gmail API

def get_latest_messages(service, processed_ids, start_time):
    results = service.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=10).execute()     #pobiera wiadomości
    messages = results.get("messages", [])      
    new_msgs = []

    for msg in messages:
        msg_id = msg["id"]
        if msg_id in processed_ids: #sprawdza, czy wiadomość była już przetworzona
            continue

        msg_data = service.users().messages().get(userId="me", id=msg_id, format="full").execute()      #pobiera szczegóły wiadomości
        internal_date = int(msg_data.get("internalDate", 0))        #sprawdza datę wiadomości

        if internal_date <= start_time:                     #tylko wiadomości po uruchomieniu skryptu
            continue

        headers = msg_data["payload"]["headers"]
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        body = ""
        parts = msg_data["payload"].get("parts", [])
        if parts:
            for part in parts:
                if part["mimeType"] == "text/plain":
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")   #dekoduje treść wiadomości(załączniki)
                    break
        else:
            body = base64.urlsafe_b64decode(msg_data["payload"]["body"]["data"]).decode("utf-8")    #jeśli nie ma załączników

        new_msgs.append((msg_id, subject, body))    #dodaje wiadomość do listy nowych wiadomości
    return new_msgs
