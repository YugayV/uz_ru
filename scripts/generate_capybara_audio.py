from gtts import gTTS
import json
import os

MANIFEST = "content/characters/capybara/manifest.json"

with open(MANIFEST, encoding="utf-8") as f:
    manifest = json.load(f)

os.makedirs("content/characters/capybara/audio", exist_ok=True)

for emotion, data in manifest["emotions"].items():
    phrases = data.get("phrases", [])
    # choose the first phrase to generate audio file for emotion
    text = phrases[0] if phrases else emotion
    out = f"content/characters/capybara/audio/{emotion}.mp3"
    tts = gTTS(text=text, lang="ru")
    tts.save(out)
    print(f"Saved {out}")
