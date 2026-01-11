import openai

import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def speech_to_text(audio_file):
    transcript = openai.audio.transcriptions.create(
        file=audio_file,
        model="whisper-1"
    )
    return transcript.text
