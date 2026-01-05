from services.deepseek_client import ask_deepseek


def ai_check(user_answer: str, correct_answer: str, age_group: str | None = None) -> str:
    """Use DeepSeek to decide whether answer is correct / almost / wrong.
    Returns one of: 'correct', 'almost', 'wrong'. In case of errors, returns 'almost' to avoid penalizing students.
    """
    prompt = f"""
You are an objective language teacher that returns exactly one word: correct / almost / wrong.
Student age group: {age_group or 'unknown'}

Correct answer: {correct_answer}
Student answer: {user_answer}

Return only one word: correct / almost / wrong
"""
    try:
        text = ask_deepseek(prompt)
        if not text:
            return "almost"
        token = text.strip().split()[0].lower()
        if token in {"correct", "almost", "wrong"}:
            return token
        # fallback: look for keywords
        if "correct" in text.lower():
            return "correct"
        if "wrong" in text.lower() or "incorrect" in text.lower():
            return "wrong"
        return "almost"
    except Exception as e:
        print(f"AI evaluator error: {e}")
        return "almost"  # be lenient on errors