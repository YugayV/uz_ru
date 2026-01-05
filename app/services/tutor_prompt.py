def build_tutor_prompt(
    age_group: str,
    language_pair: str,
    level: int,
    lesson_title: str,
    user_input: str | None
):
    # decide style
    if age_group == "kid":
        style = """
You are a cartoon tutor for small kids (4-7 years).
Rules:
- Speak very short
- Use repetition
- Never ask to read or write
- If user is silent — repeat audio
- Praise a lot
"""
    else:
        style = """
You are a calm professional tutor.
Explain briefly.
Correct mistakes.
"""

    user_phrase = user_input or ""

    # If no user input and kid mode, instruct AI to start speaking and ask the child to repeat
    extra = ""
    if age_group == "kid" and not user_input:
        extra = "\nNote: The user is a child and hasn't said anything yet. Start by saying a short phrase (e.g., 'Listen 👂 Salom. Now you say!') and then ask the child to repeat."

    # Normalize language pair into source and target
    src = tgt = language_pair
    if language_pair and '-' in language_pair:
        parts = language_pair.split('-')
        src = parts[0]
        tgt = parts[1]

    prompt = f"""
{style}

Teaching language FROM {src.upper()} TO {tgt.upper()}
Level: {level}
Lesson: {lesson_title}

User said: {user_phrase}{extra}

Rules:
- Use target language ({tgt.upper()})
- Keep phrases short and simple
- Ask only ONE question
"""
    return prompt
