import speech_recognition as sr

def speech_to_text(audio_path, lang="ru-RU"):
    r = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = r.record(source)

    try:
        return r.recognize_google(audio, language=lang)  # type: ignore
    except (sr.UnknownValueError, sr.RequestError):
        return None
