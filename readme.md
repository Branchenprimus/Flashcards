# Local Flashcards (YAML + Flask)

Small, local-only flashcard app. Upload YAML decks, pick a deck, and study with a simple Q→A flow.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run --host 127.0.0.1 --port 5000
# Open http://127.0.0.1:5000
