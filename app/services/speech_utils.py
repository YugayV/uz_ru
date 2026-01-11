def is_close_answer(user_answer: str, correct_answer: str, threshold: float = 0.8) -> bool:
    """
    Placeholder for a function to check if the user's answer is close to the correct one.
    This would typically involve NLP techniques (e.g., Levenshtein distance, fuzzy matching).
    For now, it's a simple case-insensitive exact match.
    """
    return user_answer.lower() == correct_answer.lower()