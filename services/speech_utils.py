"""Speech/text comparison utilities.

Provides a lightweight fuzzy matcher used to compare speech-to-text results
with expected answers in child-mode games.
"""
from difflib import SequenceMatcher
import re


def _normalize_text(s: str) -> str:
    if not s:
        return ""
    # Lowercase, keep letters and digits and spaces
    s = s.lower()
    s = re.sub(r"[^a-z0-9а-яё\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def similarity(a: str, b: str) -> float:
    a_n = _normalize_text(a)
    b_n = _normalize_text(b)
    if not a_n or not b_n:
        return 0.0
    return SequenceMatcher(None, a_n, b_n).ratio()


def is_close_answer(got: str, expected: str, threshold: float = 0.68) -> bool:
    """Return True when the recognized text is close enough to expected.

    - Uses SequenceMatcher ratio
    - Also accepts substring matches
    """
    if not got or not expected:
        return False
    got_n = _normalize_text(got)
    exp_n = _normalize_text(expected)
    if not got_n or not exp_n:
        return False

    if exp_n in got_n or got_n in exp_n:
        return True

    score = similarity(got_n, exp_n)
    return score >= threshold
