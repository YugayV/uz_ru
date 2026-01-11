from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json # Import the json module
from app.ai_content import generate_exercise, translate_text, generate_multiple_choice_exercise, generate_image
from app.services.session import get_or_create_web_user
from app.services.progress import get_completed_exercise_hashes, mark_exercise_as_completed, _hash_exercise # Import progress functions
from gtts import gTTS
import io

# Create a new APIRouter instance
router = APIRouter()

# Set up the template directory.
# This assumes the 'templates' directory is at the root of the project (uz_ru/templates)
TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# Define a route for the main page
@router.get("/learn", response_class=HTMLResponse)
async def get_language_selection(request: Request):
    """
    Serves the main language selection page.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/learn/{language}", response_class=HTMLResponse)
async def get_level_selection(request: Request, language: str):
    """
    Serves the level selection page for a given language.
    """
    language_map = {
        "russian": "Rus tili",
        "english": "Ingliz tili",
        "korean": "Koreys tili"
    }
    
    # Pass the language to the template
    context = {
        "request": request,
        "language_name": language_map.get(language, language.capitalize()),
        "language_slug": language
    }
    return templates.TemplateResponse("level.html", context)

def load_topics():
    """Loads topics from the JSON file."""
    topics_path = Path(__file__).resolve().parents[2] / "content" / "topics.json"
    try:
        with open(topics_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

@router.get("/learn/{language}/{level}", response_class=HTMLResponse)
async def get_topics_page(request: Request, language: str, level: str):
    """Serves the topic selection page."""
    all_topics = load_topics()
    language_topics = all_topics.get(language, [])
    
    language_map = {
        "russian": "Rus tili",
        "english": "Ingliz tili",
        "korean": "Koreys tili",
        "uzbek": "O'zbek tili"
    }
    
    context = {
        "request": request,
        "language_name": language_map.get(language, language.capitalize()),
        "language_slug": language,
        "level_slug": level,
        "topics": language_topics
    }
    return templates.TemplateResponse("topics.html", context)


@router.get("/learn/{language}/{level}/{topic}", response_class=HTMLResponse)
async def get_exercise_page(request: Request, language: str, level: str, topic: str):
    """
    Serves the main exercise page.
    This is where the AI-generated content will be displayed.
    """
    session_id = request.cookies.get("session_id")
    user, new_session_id = get_or_create_web_user(session_id)
    
    # Get completed exercises for this user
    completed_hashes = get_completed_exercise_hashes(user.id)
    
    # Generate the exercise content, excluding completed ones
    exercise_data = await generate_multiple_choice_exercise(language, level, list(completed_hashes), topic=topic)
    
    image_url = None
    # If the exercise was generated successfully, try to generate an image for it
    if exercise_data and not exercise_data.get("error"):
        visual_prompt = exercise_data.get("visual_prompt")
        if visual_prompt:
            image_url = await generate_image(visual_prompt)

    language_map = {
        "russian": "Rus tili",
        "english": "Ingliz tili",
        "korean": "Koreys tili"
    }
    level_map = {
        "beginner": "Boshlang'ich",
        "intermediate": "O'rta",
        "advanced": "Yuqori"
    }
    context = {
        "request": request,
        "language_name": language_map.get(language, language.capitalize()),
        "language_slug": language,
        "level_name": level_map.get(level, level.capitalize()),
        "level_slug": level,
        "exercise": exercise_data,
        "image_url": image_url
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
    # gTTS doesn't officially support Uzbek ('uz'), but it can often be synthesized
    # using the English voice model with Uzbek text. It's not perfect but works.
    # For 'ko' and 'ru', it has dedicated support.
    lang_to_use = lang if lang in ['en', 'ru', 'ko'] else 'en'
    
    try:
        # Create a gTTS object
        tts = gTTS(text=text, lang=lang_to_use, slow=False)
        
        # Save the audio to an in-memory file
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0) # Rewind the file pointer to the beginning
        
        # Stream the audio file back to the client
        return StreamingResponse(mp3_fp, media_type="audio/mpeg")
        
    except Exception as e:
        logger.error(f"Failed to generate TTS audio: {e}")
        return {"error": "Failed to generate audio"}

