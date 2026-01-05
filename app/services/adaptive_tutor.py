import json
import random
from pathlib import Path
from difflib import SequenceMatcher
from .character_engine import get_reaction
from .rewards import check_rewards

LESSONS_ROOT = Path(__file__).resolve().parents[1] / ".." / "data" / "lessons"


def assess_user(user):
    """Return a simple profile dict with proficiency level (1..6) and child/adult hint."""
    xp = getattr(user, "xp", 0) or 0
    level = min(6, xp // 100 + 1)

    # naive child/adult guess: if base_language set and streak small, assume child
    is_child = getattr(user, "is_child", False)

    return {"proficiency_level": level, "is_child": bool(is_child)}


def select_lesson_for_user(user, pair: str):
    profile = assess_user(user)
    level = profile["proficiency_level"]
    pair_dir = LESSONS_ROOT / pair
    path = pair_dir / f"level_{level}.json"
    if not path.exists():
        # fallback: try level 1
        path = pair_dir / "level_1.json"
        if not path.exists():
            return None

    try:
        with open(path, encoding="utf-8") as f:
            lessons = json.load(f)
    except Exception:
        return None

    # pick a lesson random or based on user's xp seed
    lesson = random.choice(lessons)
    return lesson


def evaluate_transcript(transcript: str, expected: str):
    ratio = SequenceMatcher(None, transcript.lower(), expected.lower()).ratio()
    success = ratio > 0.6
    return success, ratio


def handle_submission(user, lesson_task, transcript: str, expected: str):
    success, ratio = evaluate_transcript(transcript, expected)

    # apply simple reward logic
    mood, message, reward = get_reaction(success, getattr(user, "streak", 0) + (1 if success else 0))

    # update user
    if success:
        user.streak = (user.streak or 0) + 1
        user.xp = (user.xp or 0) + reward
    else:
        user.streak = 0

    # collect rewards
    meta_rewards = check_rewards(user)

    return {
        "success": success,
        "similarity": ratio,
        "mood": mood,
        "message": message,
        "reward": reward,
        "meta_rewards": meta_rewards,
        "streak": user.streak,
        "xp": user.xp
    }
