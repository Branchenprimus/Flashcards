import os
import uuid
from typing import Any, Dict, List, Tuple, Union

from flask import (
    Flask, render_template, request, redirect, url_for, abort, jsonify, flash
)
from werkzeug.utils import secure_filename
import yaml

# --------------------------
# Flask app configuration
# --------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-local-only")
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB upload limit
ALLOWED_EXTENSIONS = {"yml", "yaml"}

# In-memory store: token -> {"decks": [{id, title, cards:[{q,a}]}]}
IN_MEMORY_STORE: Dict[str, Dict[str, Any]] = {}

# --------------------------
# Helpers
# --------------------------
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def error_response(message: str, status: int = 400):
    return render_template("index.html", error=message), status


def _validate_card(card: Dict[str, Any], deck_title: str, idx: int) -> Tuple[bool, str]:
    if not isinstance(card, dict):
        return False, f"Card #{idx+1} in deck '{deck_title}' must be a mapping with 'q' and 'a'."
    q = card.get("q")
    a = card.get("a")
    if not isinstance(q, str) or not q.strip():
        return False, f"Card #{idx+1} in deck '{deck_title}' has empty or missing 'q'."
    if not isinstance(a, str) or not a.strip():
        return False, f"Card #{idx+1} in deck '{deck_title}' has empty or missing 'a'."
    return True, ""


def validate_and_normalize_decks(data: Union[Dict[str, Any], List[Any]]) -> List[Dict[str, Any]]:
    """
    Accepts parsed YAML (already yaml.safe_load-ed).
    Returns normalized list of decks, each: {"id": str, "title": str, "cards": [{"q":str,"a":str}, ...]}
    Raises ValueError with a human-readable message if invalid.
    """
    def normalize_single(obj: Dict[str, Any]) -> Dict[str, Any]:
        title = obj.get("title")
        cards = obj.get("cards")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Each deck must have a non-empty 'title'.")
        if not isinstance(cards, list) or not cards:
            raise ValueError(f"Deck '{title}' must have a non-empty 'cards' list.")
        norm_cards = []
        for i, c in enumerate(cards):
            ok, msg = _validate_card(c, title, i)
            if not ok:
                raise ValueError(msg)
            norm_cards.append({"q": c["q"].strip(), "a": c["a"].strip()})
        return {"id": str(uuid.uuid4()), "title": title.strip(), "cards": norm_cards}

    if isinstance(data, dict) and "decks" in data:
        decks = data.get("decks")
        if not isinstance(decks, list) or not decks:
            raise ValueError("'decks' must be a non-empty list.")
        return [normalize_single(d) for d in decks if isinstance(d, dict)]
    elif isinstance(data, dict) and ("title" in data and "cards" in data):
        return [normalize_single(data)]
    else:
        raise ValueError(
            "YAML must be either a single deck with 'title' and 'cards', "
            "or an object with 'decks: [...]'. See README for examples."
        )


# --------------------------
# Routes
# --------------------------
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "yaml_file" not in request.files:
        return error_response("No file part in the request.", 400)

    file = request.files["yaml_file"]
    if file.filename == "":
        return error_response("No selected file.", 400)

    filename = secure_filename(file.filename)
    if not allowed_file(filename):
        return error_response("Only .yml or .yaml files are accepted.", 400)

    try:
        # Parse safely
        data = yaml.safe_load(file.read())
    except yaml.YAMLError as e:
        return error_response(f"Invalid YAML: {e}", 400)

    try:
        decks = validate_and_normalize_decks(data)
    except ValueError as ve:
        return error_response(str(ve), 400)

    if not decks:
        return error_response("No valid decks found.", 400)

    token = str(uuid.uuid4())
    IN_MEMORY_STORE[token] = {"decks": decks}

    # Render deck selection page (re-using index with results)
    return render_template("index.html", token=token, decks=decks)


@app.route("/session", methods=["GET"])
def session_page():
    token = request.args.get("token", "")
    deck_id = request.args.get("deck_id", "")

    if not token or token not in IN_MEMORY_STORE:
        abort(404)
    decks = IN_MEMORY_STORE[token]["decks"]
    deck = next((d for d in decks if d["id"] == deck_id), None)
    if not deck:
        abort(404)

    return render_template("session.html", token=token, deck_id=deck_id, deck_title=deck["title"])


@app.route("/api/deck", methods=["GET"])
def api_deck():
    """
    Returns the full deck (questions and answers) for client-side session logic.
    """
    token = request.args.get("token", "")
    deck_id = request.args.get("deck_id", "")

    if not token or token not in IN_MEMORY_STORE:
        return jsonify({"error": "Invalid or expired token."}), 404
    decks = IN_MEMORY_STORE[token]["decks"]
    deck = next((d for d in decks if d["id"] == deck_id), None)
    if not deck:
        return jsonify({"error": "Deck not found."}), 404

    return jsonify({
        "deck_id": deck["id"],
        "title": deck["title"],
        "cards": deck["cards"],
        "count": len(deck["cards"])
    })


@app.errorhandler(413)
def too_large(_e):
    return error_response("File too large. Limit is 1 MB.", 413)


# Local-only run guard: bind to 127.0.0.1 by default
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
