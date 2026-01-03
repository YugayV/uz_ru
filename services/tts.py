from gtts import gTTS
import uuid
import tempfile
import os

def text_to_speech(text, lang="ru"):
    filename = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp3")
    tts = gTTS(text=text, lang=lang)
    tts.save(filename)
    return filename
