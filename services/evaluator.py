from services.eval_rules import rule_based_check
from services.ai_evaluator import ai_check


def evaluate(user_answer: str, correct_answer: str, age_group: str | None = None) -> str:
    """Combined evaluator: rule-based first, AI only when rule says 'almost'.
    For children (age_group == 'kid'), use a simplified rule:
      similarity > 0.6 -> 'correct' else 'almost'
    And promote 'almost' -> 'correct' for kids (no penalties).

    Returns: 'correct' | 'almost' | 'wrong'
    """
    # Kid-specific simplified evaluation
    if age_group == "kid":
        from services.eval_rules import similarity
        sim = similarity(user_answer, correct_answer)
        if sim > 0.6:
            return "correct"
        else:
            # kids never get 'wrong' — treat as almost (no penalty)
            return "almost"

    # Adult/general flow
    rule = rule_based_check(user_answer, correct_answer)

    if rule == "almost":
        ai_result = ai_check(user_answer, correct_answer, age_group)
        result = ai_result
    else:
        result = rule

    return result