import difflib


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def rule_based_check(user_answer: str, correct_answer: str) -> str:
    """Return one of: 'correct', 'almost', 'wrong' based on simple similarity rules."""
    user_answer = (user_answer or "").strip()
    correct_answer = (correct_answer or "").strip()

    sim = similarity(user_answer, correct_answer)

    if sim > 0.85:
        return "correct"
    if sim > 0.6:
        return "almost"
    return "wrong"