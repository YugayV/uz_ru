import json
from pathlib import Path
import pytest

GAMES_DIR = Path(__file__).resolve().parents[1] / "content" / "games"
REQUIRED = {"id", "type", "question"}
VALID_TYPES = {"guess_word", "quiz", "memory", "associations"}


def _has_answer_or_options(d: dict) -> bool:
    if "answer" in d and d.get("answer") not in (None, ""):
        return True
    if "options" in d and d.get("options"):
        return True
    return False


def test_games_json_files_exist():
    files = sorted(GAMES_DIR.glob("*.json"))
    assert files, f"No game JSON files found in {GAMES_DIR}"


def test_each_game_has_required_keys():
    for p in sorted(GAMES_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            pytest.fail(f"Failed to parse {p.name}: {e}")

        missing = REQUIRED - set(data.keys())
        assert not missing, f"{p.name} is missing keys: {missing}"

        assert _has_answer_or_options(data), (
            f"{p.name} must have 'answer' (non-empty) or non-empty 'options'"
        )

        # optional sanity: check type value if present
        if "type" in data:
            assert (
                data["type"] in VALID_TYPES
            ), f"{p.name} has unexpected type: {data['type']}"
