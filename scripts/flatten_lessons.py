"""
Flatten per-level lesson files into a single per-pair JSON file.
Usage: python scripts/flatten_lessons.py
Outputs: data/lessons/<pair>.json
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "lessons"

for pair_dir in DATA_DIR.iterdir():
    if not pair_dir.is_dir():
        continue
    all_lessons = []
    for level_file in sorted(pair_dir.glob("level_*.json")):
        try:
            with open(level_file, encoding="utf-8") as f:
                lessons = json.load(f)
                all_lessons.extend(lessons)
        except Exception as e:
            print(f"Failed to read {level_file}: {e}")

    out_file = DATA_DIR / f"{pair_dir.name}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_lessons, f, ensure_ascii=False, indent=2)
    print(f"Wrote {out_file} ({len(all_lessons)} lessons)")

print("Done.")