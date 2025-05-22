import os
import json
import re
from openai import OpenAI

class AIService:
    def __init__(self, api_key=None, base_url="https://openrouter.ai/api/v1", model="mistralai/mistral-7b-instruct"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url
        self.model = model
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def ask_llm(self, subject, body):
        prompt = f"""
Na podstawie poniższego maila wyodrębnij dane w formacie JSON. 
Użyj dokładnie i wyłącznie poniższych kluczy (nie zmieniaj ich nazw, nie dodawaj nowych, nie usuwaj żadnego):
- typ_zgłoszenia
- data_faktury
- numer_faktury
- opis_problemu
- klient (zagnieżdżony obiekt z kluczami: imię_i_nazwisko, firma, numer_telefonu)
- akcja_oczekiwana
Zachowaj spójność logiczną.

Zwróć tylko czysty JSON, bez komentarzy i tekstu opisowego. Wszystkie klucze muszą być dokładnie takie jak w przykładzie poniżej (z polskimi znakami). Jeśli nie masz danych, wpisz pusty string.

Przykład:
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content.strip()
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            else:
                print("❌ Nie udało się znaleźć poprawnego bloku JSON")
        except Exception as e:
            print("❌ Błąd LLM:", e)
        return {}
