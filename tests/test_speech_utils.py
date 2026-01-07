import pytest
from services.speech_utils import is_close_answer


def test_exact_match():
    assert is_close_answer("яблоко", "яблоко")


def test_close_match():
    assert is_close_answer("яблокo", "яблоко")
    assert is_close_answer("яблоко слон", "яблоко")


def test_not_close():
    assert not is_close_answer("собака", "яблоко")


def test_threshold():
    assert is_close_answer("hello", "helo")
