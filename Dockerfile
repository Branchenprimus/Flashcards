FROM python:3.12-slim

WORKDIR /app/flashcards

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=5000 \
    FLASK_DEBUG=0

COPY flashcards/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY flashcards/ .

EXPOSE 5000

CMD ["python", "app.py"]
