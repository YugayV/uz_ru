from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import content_generator

router = APIRouter(tags=["Translator"])

class TranslationRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str

class TranslationResponse(BaseModel):
    translated_text: str

@router.post("/translate", response_model=TranslationResponse)
def translate(request: TranslationRequest):
    """
    Translates a piece of text from a source language to a target language.
    """
    try:
        translated = content_generator.translate_text(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )
        return TranslationResponse(translated_text=translated)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
