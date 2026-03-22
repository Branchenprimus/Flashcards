# Local Flashcards (YAML + Flask)

Small flashcard app for uploading YAML decks, choosing a deck, and studying with a simple Q/A flow.

## Quick start

```bash
cd flashcards
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
# Open http://127.0.0.1:5000
```

## Docker

```bash
docker compose up --build -d
# Open http://127.0.0.1:5000
```

The container runs the app on port `5000`. Set `SECRET_KEY` in your shell before starting if you want a non-default Flask secret.

## Cloudflare Tunnel

[`cloudflared.config.tmp.yml`](/home/jan/projects/Flashcards/cloudflared.config.tmp.yml) includes an ingress rule for `flashcards.darwin-labs.org` that points to `http://localhost:5000`.
