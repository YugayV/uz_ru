from fastapi import APIRouter, UploadFile, File
import shutil
import uuid
from app.services.stt import speech_to_text

router = APIRouter(prefix="/game", tags=["Games"])

@router.post("/repeat")
async def repeat_game(
    lesson_id: str,
    expected: str,
    language: str,
    voice: UploadFile = File(...)
):
    tmp_path = f"/tmp/{uuid.uuid4()}.ogg"

    with open(tmp_path, "wb") as buffer:
        shutil.copyfileobj(voice.file, buffer)

    recognized = speech_to_text(tmp_path, language)

    success = expected.lower() in recognized

    return {
        "recognized": recognized,
        "success": success,
        "reward": 10 if success else 0
    }


