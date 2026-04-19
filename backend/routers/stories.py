import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from models.story import StoryJSON
from services import supabase_service

router = APIRouter()

_DEMO_ID = "demo"
_FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _load_demo() -> StoryJSON:
    with open(_FIXTURES_DIR / "demo_story.json") as f:
        data = json.load(f)
    return StoryJSON(**data)


@router.get("/story/{story_id}", response_model=StoryJSON)
async def get_story(story_id: str) -> StoryJSON:
    if story_id == _DEMO_ID:
        return _load_demo()

    try:
        data = await supabase_service.get_story(story_id)
    except Exception:
        # Supabase unavailable — serve demo as graceful fallback
        return _load_demo()

    if data is None:
        raise HTTPException(status_code=404, detail="Story not found")

    return StoryJSON(**data)
