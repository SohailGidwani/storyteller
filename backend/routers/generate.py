import json
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks

from models.story import GenerateRequest, GenerateResponse, StoryJSON
from services import claude_service, image_service, supabase_service

router = APIRouter()

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _get_style_key(story_type: str) -> tuple[str, str | None]:
    with open(_PROMPTS_DIR / "story_type_templates.json") as f:
        templates = json.load(f)
    st = templates["story_types"].get(story_type, {})
    return st.get("default_style", "photorealism"), st.get("default_outfit")


async def _run_images_and_patch(story: dict, photo_url: str) -> None:
    """Background task: generate images, patch URLs, flip status to complete."""
    try:
        import httpx
        async with httpx.AsyncClient() as http:
            r = await http.get(photo_url)
            r.raise_for_status()
            photo_bytes = r.content
            photo_mime = r.headers.get("content-type", "image/jpeg")
    except Exception:
        # Can't fetch photo — mark complete without images
        story["status"] = "complete"
        try:
            await supabase_service.update_story(story["story_id"], story)
        except Exception:
            pass
        return

    style_key, outfit = _get_style_key(story["story_type"])
    story_id = story["story_id"]

    async def on_image_ready(location_key: str, img_bytes: bytes) -> None:
        filename = f"{location_key}.png"
        url = await supabase_service.upload_image(img_bytes, story_id, filename)

        if location_key == "hero":
            story["hero_image_url"] = url
            await supabase_service.update_story(story_id, story)
            return

        if location_key.startswith("scene_"):
            # location_key = "scene_{scene_id}_img{n}" e.g. "scene_scene_1_img1"
            remainder = location_key[len("scene_"):]        # "scene_1_img1"
            img_idx = remainder.rfind("_img")               # finds last "_img"
            scene_id = remainder[:img_idx]                  # "scene_1"
            img_tag = remainder[img_idx + 1:]               # "img1"
            img_n = int(img_tag.replace("img", "")) - 1     # 0-indexed
            count = 0
            for scene in story["scenes"]:
                if scene["scene_id"] == scene_id:
                    for block in scene["text_blocks"]:
                        if block["type"] == "image_slot":
                            if count == img_n:
                                block["image_url"] = url
                                break
                            count += 1

        elif location_key.startswith("entity_"):
            # location_key = "entity_{scene_id}_{entity_id}" e.g. "entity_scene_1_ent_gate_1"
            remainder = location_key[len("entity_"):]       # "scene_1_ent_gate_1"
            parts = remainder.split("_", 2)                 # ["scene", "1", "ent_gate_1"]
            scene_id = f"{parts[0]}_{parts[1]}"             # "scene_1"
            entity_id = parts[2]                            # "ent_gate_1"
            for scene in story["scenes"]:
                if scene["scene_id"] == scene_id:
                    for ent in scene["clickable_entities"]:
                        if ent["entity_id"] == entity_id:
                            ent["image_url"] = url

        await supabase_service.update_story(story_id, story)

    await image_service.run_image_pipeline(
        story, photo_bytes, photo_mime, style_key, outfit, on_image_ready
    )

    # All images done — flip to complete
    story["status"] = "complete"
    try:
        await supabase_service.update_story(story_id, story)
    except Exception:
        pass


@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest, background_tasks: BackgroundTasks) -> GenerateResponse:
    story = await claude_service.generate_story(
        child_name=req.child_name,
        age=req.age,
        photo_url=req.photo_url,
        story_type=req.story_type,
        adhd=req.adhd,
        gender=req.gender,
    )

    # Save with status "generating" — images not ready yet
    story["status"] = "generating"
    try:
        await supabase_service.save_story(story)
    except Exception:
        pass

    background_tasks.add_task(_run_images_and_patch, story, req.photo_url)

    return GenerateResponse(
        story_id=story["story_id"],
        status="generating",
        story=StoryJSON(**story),
    )
