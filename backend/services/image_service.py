"""
Image generation service.

Primary: Gemini gemini-2.5-flash-image (image-to-image via google-genai)
Fallback: DALL-E 3 via OpenAI API

NOTE: CLAUDE.md references NanoBanana but StoryWorld/image_pipeline.py uses Gemini.
      This service uses Gemini as primary. Swap if NanoBanana credentials arrive.
"""

import asyncio
import json
import os
from pathlib import Path

# ── STYLE BLOCK ──────────────────────────────────────────

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_style_blocks: dict | None = None


def _get_style_blocks() -> dict:
    global _style_blocks
    if _style_blocks is None:
        with open(_PROMPTS_DIR / "story_type_templates.json") as f:
            _style_blocks = json.load(f)["style_blocks"]
    return _style_blocks


def build_style_string(style_key: str, outfit: str | None = None) -> str:
    s = _get_style_blocks()[style_key]
    parts = [
        f"Art style: {s['rendering']}.",
        f"Color palette: {s['palette']}.",
        f"Lighting: {s['lighting']}.",
        f"Atmosphere: {s['atmosphere']}.",
        f"Camera: {s['camera']}.",
        f"Texture: {s['texture']}.",
    ]
    if outfit:
        parts.append(f"The child is wearing: {outfit}. This outfit does not change between scenes.")
    parts.append("Maintain exact visual consistency with all other images in this series.")
    return " ".join(parts)


# ── GEMINI (PRIMARY) ─────────────────────────────────────

async def _generate_gemini(
    prompt_text: str,
    photo_bytes: bytes | None,
    photo_mime: str = "image/jpeg",
) -> bytes:
    from google import genai
    from google.genai import types

    api_key = os.environ["GOOGLE_AI_API_KEY"]
    client = genai.Client(api_key=api_key)

    contents = []
    if photo_bytes:
        contents.append(types.Part.from_bytes(data=photo_bytes, mime_type=photo_mime))
    contents.append(prompt_text)

    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash-image",
        contents=contents,
        config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            return part.inline_data.data

    raise RuntimeError("Gemini returned no image data")


# ── DALL-E (FALLBACK) ────────────────────────────────────

async def _generate_dalle(prompt_text: str) -> bytes:
    import httpx
    from openai import AsyncOpenAI

    client = AsyncOpenAI()
    response = await client.images.generate(
        model="dall-e-3",
        prompt=prompt_text[:4000],
        size="1024x1024",
        response_format="url",
    )
    image_url = response.data[0].url
    async with httpx.AsyncClient() as http:
        r = await http.get(image_url)
        r.raise_for_status()
        return r.content


# ── PUBLIC API ───────────────────────────────────────────

async def generate_image(
    prompt_text: str,
    photo_bytes: bytes | None = None,
    photo_mime: str = "image/jpeg",
) -> bytes | None:
    """
    Try Gemini first, fall back to DALL-E, return None if both fail.
    Never raises — image failure must not block story delivery.
    """
    try:
        return await _generate_gemini(prompt_text, photo_bytes, photo_mime)
    except Exception:
        pass

    try:
        return await _generate_dalle(prompt_text)
    except Exception:
        return None


MAX_IMAGES_PER_STORY = 8


async def run_image_pipeline(
    story: dict,
    photo_bytes: bytes,
    photo_mime: str,
    style_key: str,
    outfit: str | None,
    on_image_ready: callable,
) -> None:
    """
    Generate images in priority order: hero → scene images → entity images.
    Hard cap at MAX_IMAGES_PER_STORY (8) so demo generation stays fast.
    """
    style_string = build_style_string(style_key, outfit)
    child_name = story.get("child_name", "Child")
    generated = 0

    # 1. Hero portrait
    hero_prompt = (
        f"Using this child's exact likeness and features, generate a portrait illustration. "
        f"Scene: A child standing confidently in a magical setting, looking directly at the viewer with a warm smile. "
        f"This is {child_name}, the hero of this story. "
        f"Style: {style_string}"
    )
    hero_bytes = await generate_image(hero_prompt, photo_bytes, photo_mime)
    if hero_bytes:
        await on_image_ready("hero", hero_bytes)
        generated += 1

    # 2. Scene images (highest priority after hero)
    for scene in story.get("scenes", []):
        if generated >= MAX_IMAGES_PER_STORY:
            break
        sid = scene["scene_id"]
        img_count = 0
        for block in scene.get("text_blocks", []):
            if block["type"] == "image_slot":
                if generated >= MAX_IMAGES_PER_STORY:
                    break
                img_count += 1
                scene_prompt = (
                    f"Using this child's exact likeness and features, generate an illustration. "
                    f"Scene: {block['prompt']} "
                    f"Style: {style_string}"
                )
                img_bytes = await generate_image(scene_prompt, photo_bytes, photo_mime)
                if img_bytes:
                    await on_image_ready(f"scene_{sid}_img{img_count}", img_bytes)
                    generated += 1

    # 3. Entity images — only if budget remains
    for scene in story.get("scenes", []):
        if generated >= MAX_IMAGES_PER_STORY:
            break
        sid = scene["scene_id"]
        for ent in scene.get("clickable_entities", []):
            if generated >= MAX_IMAGES_PER_STORY:
                break
            ent_prompt = (
                f"Generate an illustration of this object/creature/location. "
                f"Subject: {ent['image_prompt']} "
                f"Style: {style_string}"
            )
            img_bytes = await generate_image(ent_prompt, None)
            if img_bytes:
                await on_image_ready(f"entity_{sid}_{ent['entity_id']}", img_bytes)
                generated += 1
