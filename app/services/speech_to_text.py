import openai
import re

import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def speech_to_text(audio_file):
    transcript = openai.audio.transcriptions.create(
        file=audio_file,
        model="whisper-1"
    )
    
    text = transcript.text
    # Remove emojis, punctuation, and special characters, keeping letters, numbers, and spaces
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    
    return text
