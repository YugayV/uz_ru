from services.eval_rules import rule_based_check


def test_rule_exact_match():
    assert rule_based_check("Salom", "Salom") == "correct"


def test_rule_punctuation():
    assert rule_based_check("Salom!", "Salom") == "correct"


def test_rule_small_typo():
    assert rule_based_check("Salam", "Salom") == "almost"


def test_rule_wrong():
    assert rule_based_check("Hello", "Salom") == "wrong"


def test_kid_evaluation_exact():
    from services.evaluator import evaluate
    assert evaluate("Salom", "Salom", "kid") == "correct"


def test_kid_evaluation_silence():
    from services.evaluator import evaluate
    # silence -> almost (no penalty in routes)
    assert evaluate("", "Salom", "kid") == "almost"