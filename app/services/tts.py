from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def text_to_speech(text: str):
    audio = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text
    )
    return audio
