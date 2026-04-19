import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException

from models.story import GenerateRequest, GenerateResponse, StoryJSON
from services import claude_service, image_service, supabase_service

router = APIRouter()

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _get_style_key(story_type: str) -> tuple[str, str | None]:
    """Return (style_key, outfit) for a story type."""
    with open(_PROMPTS_DIR / "story_type_templates.json") as f:
        templates = json.load(f)
    st = templates["story_types"].get(story_type, {})
    return st.get("default_style", "photorealism"), st.get("default_outfit")


async def _run_images_and_patch(story: dict, photo_url: str) -> None:
    """Background task: generate images and patch URLs back onto the stored story."""
    try:
        import httpx
        async with httpx.AsyncClient() as http:
            r = await http.get(photo_url)
            r.raise_for_status()
            photo_bytes = r.content
            photo_mime = r.headers.get("content-type", "image/jpeg")
    except Exception:
        return  # can't fetch photo — skip images silently

    style_key, outfit = _get_style_key(story["story_type"])
    story_id = story["story_id"]

    async def on_image_ready(location_key: str, img_bytes: bytes) -> None:
        filename = f"{location_key}.png"
        url = await supabase_service.upload_image(img_bytes, story_id, filename)

        # Patch the in-memory story dict
        if location_key == "hero":
            story["hero_image_url"] = url
            return

        parts = location_key.split("_", 2)
        if parts[0] == "scene":
            # "scene_{scene_id}_img{n}" → find the nth image_slot in scene
            _, scene_id, img_tag = location_key.split("_", 2)
            img_n = int(img_tag.replace("img", "")) - 1
            count = 0
            for scene in story["scenes"]:
                if scene["scene_id"] == scene_id:
                    for block in scene["text_blocks"]:
                        if block["type"] == "image_slot":
                            if count == img_n:
                                block["image_url"] = url
                                break
                            count += 1
        elif parts[0] == "entity":
            _, scene_id, entity_id = location_key.split("_", 2)
            for scene in story["scenes"]:
                if scene["scene_id"] == scene_id:
                    for ent in scene["clickable_entities"]:
                        if ent["entity_id"] == entity_id:
                            ent["image_url"] = url

        # Persist updated story to Supabase after each image
        await supabase_service.update_story(story_id, story)

    await image_service.run_image_pipeline(
        story, photo_bytes, photo_mime, style_key, outfit, on_image_ready
    )


@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest, background_tasks: BackgroundTasks) -> GenerateResponse:
    story = await claude_service.generate_story(
        child_name=req.child_name,
        age=req.age,
        photo_url=req.photo_url,
        story_type=req.story_type,
        adhd=req.adhd,
    )

    try:
        await supabase_service.save_story(story)
    except Exception:
        pass  # don't fail the request if DB write fails

    background_tasks.add_task(_run_images_and_patch, story, req.photo_url)

    return GenerateResponse(
        story_id=story["story_id"],
        status=story["status"],
        story=StoryJSON(**story),
    )
