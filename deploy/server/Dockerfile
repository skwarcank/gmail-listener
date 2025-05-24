FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Skopiuj pliki projektu (dostosuj ścieżkę jeśli budujesz z innego katalogu)
COPY ../../ /app/

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "server.py"]