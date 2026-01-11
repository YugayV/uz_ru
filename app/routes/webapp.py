import logging # NEW: Import logging
import os
import io
import json
import re
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse, Response
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.ai_content import translate_text, generate_multiple_choice_exercise, generate_image # Removed generate_exercise
from app.services.session import get_or_create_web_user
from app.services.progress import get_completed_exercise_hashes, mark_exercise_as_completed, _hash_exercise
from gtts import gTTS

logger = logging.getLogger(__name__) # NEW: Initialize logger

router = APIRouter()

def clean_text_for_tts(text: str) -> str:
    """Removes emojis and other non-verbal characters for cleaner TTS output."""
    if not isinstance(text, str):
        return ""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251" 
        "]+",
        flags=re.UNICODE,
    )
    cleaned_text = emoji_pattern.sub(r'', text)
    # Removing aggressive cleaning that was stripping non-Latin characters
    # cleaned_text = re.sub(r'[^\w\s]', '', cleaned_text)
    return cleaned_text.strip()

# Set up the template directory.
TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

def load_topics():
    """Loads topics from the JSON file."""
    topics_path = Path(__file__).resolve().parents[2] / "content" / "topics.json"
    try:
        with open(topics_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Topics file not found at {topics_path}")
        return {}


# Define a route for the main page (native language selection)
@router.get("/", response_class=HTMLResponse)
async def get_native_language_selection(request: Request):
    """Serves the initial page for native language selection."""
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/learn/native/{native_lang_slug}", response_class=HTMLResponse)
async def get_learn_language_selection(request: Request, native_lang_slug: str):
    """
    Serves the page for selecting the language to learn, after native language is chosen.
    """
    language_map = {
        "russian": "Rus tili",
        "english": "Ingliz tili",
        "korean": "Koreys tili",
        "uzbek": "O'zbek tili"
    }

    context = {
        "request": request,
        "native_language_name": language_map.get(native_lang_slug, native_lang_slug.capitalize()),
        "native_language_slug": native_lang_slug
    }
    return templates.TemplateResponse("learn_language_selection.html", context)


@router.get("/learn/{native_lang_slug}/{learn_lang_slug}", response_class=HTMLResponse)
async def get_level_selection(request: Request, native_lang_slug: str, learn_lang_slug: str):
    """
    Serves the level selection page for a given language.
    """
    language_map = {
        "russian": "Rus tili",
        "english": "Ingliz tili",
        "korean": "Koreys tili",
        "uzbek": "O'zbek tili"
    }
    
    context = {
        "request": request,
        "native_language_name": language_map.get(native_lang_slug, native_lang_slug.capitalize()),
        "native_language_slug": native_lang_slug,
        "learn_language_name": language_map.get(learn_lang_slug, learn_lang_slug.capitalize()),
        "learn_language_slug": learn_lang_slug
    }
    return templates.TemplateResponse("level.html", context)


@router.get("/learn/{native_lang_slug}/{learn_lang_slug}/{level}", response_class=HTMLResponse)
async def get_topics_page(request: Request, native_lang_slug: str, learn_lang_slug: str, level: str):
    """Serves the topic selection page."""
    all_topics = load_topics()
    language_topics = all_topics.get(learn_lang_slug, []) # Topics based on language to learn
    
    language_map = {
        "russian": "Rus tili",
        "english": "Ingliz tili",
        "korean": "Koreys tili",
        "uzbek": "O'zbek tili"
    }
    
    context = {
        "request": request,
        "native_language_name": language_map.get(native_lang_slug, native_lang_slug.capitalize()),
        "native_language_slug": native_lang_slug,
        "learn_language_name": language_map.get(learn_lang_slug, learn_lang_slug.capitalize()),
        "learn_language_slug": learn_lang_slug,
        "level_slug": level,
        "topics": language_topics
    }
    return templates.TemplateResponse("topics.html", context)


@router.get("/learn/{native_lang_slug}/{learn_lang_slug}/{level}/{topic}", response_class=HTMLResponse)
async def get_exercise_page(request: Request, native_lang_slug: str, learn_lang_slug: str, level: str, topic: str):
    """
    Serves the main exercise page.
    This is where the AI-generated content will be displayed.
    """
    session_id = request.cookies.get("session_id")
    user, new_session_id = get_or_create_web_user(session_id)
    
    # Get completed exercises for this user
    completed_hashes = get_completed_exercise_hashes(user.id)
    
    # Generate the exercise content, excluding completed ones and based on the topic
    # Questions will be in native language, answers in the language being learned
    exercise_data = await generate_multiple_choice_exercise(learn_lang_slug, native_lang_slug, level, topic, list(completed_hashes))
    
    image_url = None
    # If the exercise was generated successfully, try to generate an image for it
    if exercise_data and not exercise_data.get("error"):
        visual_prompt = exercise_data.get("visual_prompt")
        if visual_prompt:
            image_url = await generate_image(visual_prompt)

    language_map = {
        "russian": "Rus tili",
        "english": "Ingliz tili",
        "korean": "Koreys tili",
        "uzbek": "O'zbek tili"
    }
    level_map = {
        "beginner": "Boshlang'ich",
        "intermediate": "O'rta",
        "advanced": "Yuqori"
    }
    context = {
        "request": request,
        "native_language_name": language_map.get(native_lang_slug, native_lang_slug.capitalize()),
        "native_language_slug": native_lang_slug,
        "learn_language_name": language_map.get(learn_lang_slug, learn_lang_slug.capitalize()),
        "learn_language_slug": learn_lang_slug,
        "level_name": level_map.get(level, level.capitalize()),
        "level_slug": level,
        "exercise": exercise_data,
        "image_url": image_url,
        "topic": topic # Pass topic to template
    }
    
    # Store the hash of the current exercise in the user's session to mark it as completed later
    if exercise_data and not exercise_data.get("error"):
        current_hash = _hash_exercise(exercise_data)
        request.session['current_exercise_hash'] = current_hash

    response = templates.TemplateResponse("exercise.html", context)
    # If a new session was created, set the cookie in the user's browser
    if new_session_id:
        response.set_cookie(key="session_id", value=new_session_id, httponly=True, max_age=365*24*60*60) # Cookie for 1 year
    
    return response

@router.get("/translator", response_class=HTMLResponse)
async def get_translator_page(request: Request):
    """Serves the translator page."""
    return templates.TemplateResponse("translator.html", {"request": request, "translation_result": ""})

@router.post("/mark_completed")
async def mark_completed(request: Request):
    """Marks the current exercise as completed for the user."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        return {"status": "error", "message": "No session found"}

    user, _ = get_or_create_web_user(session_id)
    
    # We retrieve the hash from the server-side session for security
    current_hash = request.session.get('current_exercise_hash')

    if user and current_hash:
        # This is a simplified way to pass the data to be marked.
        # A more robust way would be to re-hash the data sent from the client.
        mark_exercise_as_completed(user.id, {"question": current_hash}) # We pass a dummy dict with the hash's source
        
        # Clear the hash from the session
        request.session.pop('current_exercise_hash', None)
        
        return {"status": "ok"}
    
    return {"status": "error", "message": "User or exercise hash not found"}


@router.post("/translator", response_class=HTMLResponse)
async def handle_translation(request: Request):
    """Handles the translation request."""
    form_data = await request.form()
    text_to_translate = form_data.get("text_to_translate")
    target_language = form_data.get("target_language")

    translation = ""
    if text_to_translate and target_language:
        translation = await translate_text(text_to_translate, target_language)

    context = {
        "request": request,
        "translation_result": translation,
        "original_text": text_to_translate,
        "target_lang": target_language
    }
    
    return templates.TemplateResponse("translator.html", context)

@router.get("/tts")
async def text_to_speech(text: str, lang: str = 'en'):
    """
    Generates an audio file from text and returns it as a streaming response.
    Supports 'en', 'ru', 'ko', and 'uz'.
    """
    lang_to_use = lang if lang in ['en', 'ru', 'ko'] else 'en'
    
    # Clean the text before generating audio
    cleaned_text = clean_text_for_tts(text)

    if not cleaned_text:
        logger.warning("No text to speak after cleaning.") # Changed print to logger.warning
        return Response(status_code=204) # Return No Content if nothing to speak

    try:
        tts = gTTS(text=cleaned_text, lang=lang_to_use, slow=True)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return StreamingResponse(mp3_fp, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Failed to generate TTS audio: {e}", exc_info=True) # Added exc_info
        return Response(status_code=500, content="Failed to generate audio") # Return proper error