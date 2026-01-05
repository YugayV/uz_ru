import tempfile
import os
from pydub import AudioSegment
import speech_recognition as sr


def voice_to_text(file_path: str, language_code: str = "ru-RU") -> str:
    """
    Convert an OGG/OPUS file to WAV and transcribe to text using Google Web Speech API.
    Returns empty string on failure.
    Note: Requires ffmpeg binary available for pydub to convert audio.
    """
    try:
        # Convert to wav using pydub
        sound = AudioSegment.from_file(file_path)
        wav_fd, wav_path = tempfile.mkstemp(suffix=".wav")
        os.close(wav_fd)
        sound.export(wav_path, format="wav")

        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = r.record(source)

        try:
            text = r.recognize_google(audio, language=language_code)
            return text
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            print(f"STT error (recognize): {e}")
            return ""
        finally:
            try:
                os.remove(wav_path)
            except Exception:
                pass
    except Exception as e:
        print(f"STT conversion error: {e}")
        return ""
