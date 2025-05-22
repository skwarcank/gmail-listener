import os 
import json 
import re
from openai import OpenAI

#inicjalizacja klienta OpenAI
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
        response = client.chat.completions.create(              #wysłanie zapytania do LLM
            model="mistralai/mistral-7b-instruct",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()   #Przetwarzanie odpowiedzi
        match = re.search(r"\{.*\}", content, re.DOTALL)        #Dopasowanie odpowiedzi do wzorca JSON
        if match:
            return json.loads(match.group(0))
        else:
            print("❌ Nie udało się znaleźć poprawnego bloku JSON")
    except Exception as e:                                      #obsługa błędów
        print("❌ Błąd LLM:", e)
    return {}
