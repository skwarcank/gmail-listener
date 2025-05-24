import os
import requests

class DBService:
    def __init__(self, api_key=None, base_id=None, table_name=None):
        # Pobiera dane konfiguracyjne z argumentów lub zmiennych środowiskowych
        self.api_key = api_key or os.getenv("AIRTABLE_API_KEY")
        self.base_id = base_id or os.getenv("AIRTABLE_BASE_ID")
        self.table_name = table_name or os.getenv("AIRTABLE_TABLE_NAME")
        # Buduje URL do API Airtable na podstawie konfiguracji
        self.api_url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}"
        # Sprawdza, czy wszystkie wymagane dane są dostępne
        if not all([self.api_key, self.base_id, self.table_name]):
            raise ValueError("Ustaw AIRTABLE_API_KEY, AIRTABLE_BASE_ID i AIRTABLE_TABLE_NAME jako zmienne środowiskowe lub przekaż do konstruktora.")

    def insert_row(self, data):
        # Przygotowuje słownik pól do wysłania do Airtable na podstawie danych wejściowych
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
        # Przygotowuje nagłówki HTTP z autoryzacją do API Airtable
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Tworzy payload do wysłania w żądaniu POST
        payload = {"fields": fields}
        # Wysyła żądanie POST do Airtable z danymi
        response = requests.post(self.api_url, json=payload, headers=headers)
        # Sprawdza odpowiedź i wypisuje odpowiedni komunikat
        if response.status_code == 200 or response.status_code == 201:
            print("✅ Zapisano do Airtable")
        else:
            print(f"❌ Błąd zapisu do Airtable: {response.status_code} {response.text}")