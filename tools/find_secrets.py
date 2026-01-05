import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9_-]{20,}"), 'OpenAI/DeepSeek-like API keys (sk-)'),
    (re.compile(r"[0-9]{9}:[A-Za-z0-9_-]{35,}"), 'Telegram bot token'),
]

IGNORE = ['venv', '.git', 'node_modules']

if __name__ == '__main__':
    found = []
    for p in ROOT.rglob('*'):
        if any(part in IGNORE for part in p.parts):
            continue
        if not p.is_file():
            continue
        try:
            text = p.read_text(errors='ignore')
        except Exception:
            continue
        for pattern, desc in PATTERNS:
            for m in pattern.finditer(text):
                found.append((p.relative_to(ROOT), desc, m.group(0)))

    if found:
        print('Potential secrets found:')
        for f, desc, key in found:
            print(f' - {f}: {desc} -> {key}')
        raise SystemExit(1)
    else:
        print('No obvious secrets found.')
