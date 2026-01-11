from fastapi import APIRouter, HTTPException
from app.services import content_generator

router = APIRouter(prefix="/lessons", tags=["Lessons V2 - Dynamic Content"])

@router.get("/topics/{pair}/{level}", response_model=list[str])
def get_topics_for_level(pair: str, level: int):
    """
    Generates and returns a list of learning topics for a given language pair and level.
    `pair` should be in `uz-ru`, `uz-en`, or `uz-ko` format.
    """
    try:
        topics = content_generator.generate_topics(pair=pair, level=level)
        return topics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/games/{pair}/{level}/{topic}")
def get_games_for_topic(pair: str, level: int, topic: str):
    """
    Generates and returns a list of games/exercises for a specific topic.
    """
    try:
        games = content_generator.generate_games_for_topic(
            pair=pair, level=level, topic=topic
        )
        return games
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    path = content_dir / pair_key / f"level_{level}.json"

    if not path.exists():
        raise HTTPException(status_code=404, detail="Lessons not found")

    with open(path, encoding="utf-8") as f:
        lessons = json.load(f)

    if kids:
        try:
            from app.routes.public_lessons import filter_for_kids
            lessons = [filter_for_kids(l) for l in lessons]
        except Exception:
            # If the filter helper is not available for any reason, do a minimal filter
            filtered = []
            for l in lessons:
                l2 = dict(l)
                l2['tasks'] = [t for t in l.get('tasks', []) if t.get('type') in ['listen', 'repeat', 'choose_sound']]
                filtered.append(l2)
            lessons = filtered

    return lessons
