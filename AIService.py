import os
import json
import re
from openai import OpenAI
from langfuse import Langfuse

class AIService:
    def __init__(self, api_key=None, base_url="https://openrouter.ai/api/v1", model="mistralai/mistral-7b-instruct"):
        # Inicjalizacja kluczy i parametrów modelu LLM oraz klienta OpenAI i Langfuse
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url
        self.model = model
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST"),
        )

    def get_prompt(self, prompt_name, **kwargs):
        # Pobiera prompt o zadanej nazwie z Langfuse i renderuje go z przekazanymi parametrami
        prompt = self.langfuse.get_prompt(prompt_name)
        prompt_template = prompt.prompt  # zawiera np. "Subject: {subject}\nBody: {body}"
        return prompt_template.format(**kwargs)

    def ask_llm(self, subject, body, trace=None):
        # Przygotowuje prompt na podstawie szablonu i danych wejściowych
        prompt = self.get_prompt("extract_mail_json", subject=subject, body=body)
        response_data = {}
        try:
            # Jeśli przekazano trace, rejestruje wywołanie LLM jako span w Langfuse
            span_id = None
            if trace is not None:
                span = self.langfuse.span(
                    name="llm_call",
                    input={"prompt": prompt, "subject": subject, "body": body},
                    trace_id=trace.id
                )
                span_id = span.id

            # Wywołuje model LLM z przygotowanym promptem
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            # Przetwarza odpowiedź LLM, wyciąga blok JSON z odpowiedzi
            content = response.choices[0].message.content.strip()
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                response_data = json.loads(match.group(0))
            else:
                print("❌ Nie udało się znaleźć poprawnego bloku JSON")
            
            # Jeśli trace i span istnieją, zapisuje output do Langfuse
            if trace is not None and span_id is not None:
                self.langfuse.span(
                    name="llm_call",
                    output=response_data,
                    trace_id=trace.id,
                    parent_id=span_id
                )
        except Exception as e:
            # Obsługa błędów podczas wywołania LLM lub przetwarzania odpowiedzi
            print("❌ Błąd LLM:", e)
        return response_data

