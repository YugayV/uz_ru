import json
import os

# Prefer Coqui TTS if available, otherwise fall back to gTTS
try:
    from TTS.api import TTS
    _tts = TTS("tts_models/en/ljspeech/tacotron2-DDC")
    def synth(text, path):
        _tts.tts_to_file(text=text, file_path=path)
except Exception:
    from gtts import gTTS
    def synth(text, path):
        tts = gTTS(text=text, lang="en")
        tts.save(path)

LESSON_PATH = "content/en/a0"

for file in os.listdir(LESSON_PATH):
    with open(f"{LESSON_PATH}/{file}", encoding="utf-8") as f:
        lesson = json.load(f)

    phrase = lesson.get("content", {}).get("phrase") or lesson.get("phrase") or ""
    audio_path = f"audio/en/a0/{lesson.get('id', os.path.splitext(file)[0])}.mp3"

    os.makedirs(os.path.dirname(audio_path), exist_ok=True)

    synth(phrase, audio_path)

    lesson["audio"] = {"phrase": audio_path}

    with open(f"{LESSON_PATH}/{file}", "w", encoding="utf-8") as f:
        json.dump(lesson, f, ensure_ascii=False, indent=2)
