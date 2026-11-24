import json
from pathlib import Path

SAVE_PATH = Path(__file__).resolve().parent.parent / "save.json"


def load_progress(path=SAVE_PATH):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return {int(k): int(v) for k, v in data.get("stars", {}).items()}
    except (OSError, ValueError, AttributeError):
        return {}


def save_progress(stars, path=SAVE_PATH):
    payload = {"stars": {str(k): v for k, v in sorted(stars.items())}}
    try:
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def is_unlocked(stars, index):
    return index == 0 or stars.get(index - 1, 0) > 0
