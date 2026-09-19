FROM python:3.12-slim

WORKDIR /app
COPY services/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все сервисы: SERVICE_MODULE ниже выбирает, какой из них запустить.
COPY services/ .
ENV PYTHONUNBUFFERED=1
CMD ["sh", "-c", "uvicorn ${SERVICE_MODULE}.main:app --host 0.0.0.0 --port ${PORT}"]