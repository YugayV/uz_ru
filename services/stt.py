import whisper

model = whisper.load_model("base")  # можно tiny для скорости

def speech_to_text(audio_path: str, language: str) -> str:
    result = model.transcribe(
        audio_path,
        language=language.lower()
    )
    return result["text"].strip().lower()
