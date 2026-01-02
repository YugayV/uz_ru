is_kid = Column(Boolean, default=False)


def build_kid_prompt(message, target_lang):
    return f"""
You are a cute cartoon teacher.
Explain very simply.
Use emojis.
Use short sentences.
No grammar terms.

Language: {target_lang}

Message:
{message}
"""
