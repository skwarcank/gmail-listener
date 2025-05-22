import os
import requests

class DBService:
    def __init__(self, api_key=None, base_id=None, table_name=None):
        self.api_key = api_key or os.getenv("AIRTABLE_API_KEY")
        self.base_id = base_id or os.getenv("AIRTABLE_BASE_ID")
        self.table_name = table_name or os.getenv("AIRTABLE_TABLE_NAME")
        self.api_url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}"
        if not all([self.api_key, self.base_id, self.table_name]):
            raise ValueError("Ustaw AIRTABLE_API_KEY, AIRTABLE_BASE_ID i AIRTABLE_TABLE_NAME jako zmienne środowiskowe lub przekaż do konstruktora.")

    def insert_row(self, data):
        # Dopasuj strukturę do swojej tabeli!
        fields = {
            "typ_zgłoszenia": data.get("typ_zgłoszenia"),
            "data_faktury": data.get("data_faktury"),
            "numer_faktury": data.get("numer_faktury"),
            "opis_problemu": data.get("opis_problemu"),
            "imię_i_nazwisko": data.get("klient", {}).get("imię_i_nazwisko"),
            "firma": data.get("klient", {}).get("firma"),
            "numer_telefonu": data.get("klient", {}).get("numer_telefonu"),
            "akcja_oczekiwana": data.get("akcja_oczekiwana"),
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {"fields": fields}
        response = requests.post(self.api_url, json=payload, headers=headers)
        if response.status_code == 200 or response.status_code == 201:
            print("✅ Zapisano do Airtable")
        else:
            print(f"❌ Błąd zapisu do Airtable: {response.status_code} {response.text}")