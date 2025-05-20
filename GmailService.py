import os
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

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
