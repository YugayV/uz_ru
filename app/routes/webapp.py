from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.ai_content import generate_exercise, translate_text, generate_multiple_choice_exercise

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

@router.get("/learn/{language}/{level}", response_class=HTMLResponse)
async def get_exercise_page(request: Request, language: str, level: str):
    """
    Serves the main exercise page.
    This is where the AI-generated content will be displayed.
    """
    # Generate the exercise content using the new function
    exercise_data = await generate_multiple_choice_exercise(language, level)

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
        "exercise": exercise_data # Pass the entire exercise object
    }
    return templates.TemplateResponse("exercise.html", context)

@router.get("/translator", response_class=HTMLResponse)
async def get_translator_page(request: Request):
    """Serves the translator page."""
    return templates.TemplateResponse("translator.html", {"request": request, "translation_result": ""})

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

