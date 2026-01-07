#!/usr/bin/env python3
from pathlib import Path
import json
import sys

GAMES_DIR = Path(__file__).resolve().parents[1] / "content" / "games"
REQUIRED = {"id", "type", "question"}
VALID_TYPES = {"guess_word", "quiz", "memory", "associations"}

errors = []
for p in sorted(GAMES_DIR.glob('*.json')):
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
    except Exception as e:
        errors.append(f"{p.name}: parse error: {e}")
        continue

    missing = REQUIRED - set(data.keys())
    if missing:
        errors.append(f"{p.name}: missing keys: {missing}")

    has_answer = 'answer' in data and data.get('answer') not in (None, "")
    has_options = 'options' in data and data.get('options') not in (None, [], "")
    if not (has_answer or has_options):
        errors.append(f"{p.name}: must have non-empty 'answer' or non-empty 'options'")

    if 'type' in data and data['type'] not in VALID_TYPES:
        errors.append(f"{p.name}: unexpected type: {data['type']}")

if errors:
    print("Found errors in game manifests:")
    for e in errors:
        print(" - " + e)
    sys.exit(1)

print("All game JSON files look OK")
sys.exit(0)
