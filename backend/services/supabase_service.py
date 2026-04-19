"""Supabase DB and Storage operations."""

import json
import os
import uuid

from supabase import AsyncClient, acreate_client

_db_client: AsyncClient | None = None
_storage_client: AsyncClient | None = None


async def _get_db_client() -> AsyncClient:
    """Anon key client — used for table reads/writes (RLS applies)."""
    global _db_client
    if _db_client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_KEY"]
        _db_client = await acreate_client(url, key)
    return _db_client


async def _get_storage_client() -> AsyncClient:
    """Service role key client — used for storage uploads (bypasses RLS)."""
    global _storage_client
    if _storage_client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ.get("SUPABASE_SERVICE_KEY", os.environ["SUPABASE_KEY"])
        _storage_client = await acreate_client(url, key)
    return _storage_client


STORIES_TABLE = "stories"
PHOTOS_BUCKET = "photos"
IMAGES_BUCKET = "story-images"


# ── STORIES ──────────────────────────────────────────────

async def save_story(story: dict) -> str:
    """Insert story JSON into Supabase. Returns story_id."""
    client = await _get_db_client()
    await client.table(STORIES_TABLE).insert({
        "id": story["story_id"],
        "status": story["status"],
        "story_json": json.dumps(story),
    }).execute()
    return story["story_id"]


async def get_story(story_id: str) -> dict | None:
    """Fetch story JSON by ID. Returns None if not found."""
    client = await _get_db_client()
    result = await client.table(STORIES_TABLE).select("story_json").eq("id", story_id).single().execute()
    if not result.data:
        return None
    return json.loads(result.data["story_json"])


async def update_story(story_id: str, story: dict) -> None:
    """Overwrite the story_json for an existing row."""
    client = await _get_db_client()
    await client.table(STORIES_TABLE).update({
        "status": story.get("status", "complete"),
        "story_json": json.dumps(story),
    }).eq("id", story_id).execute()


# ── STORAGE ──────────────────────────────────────────────

async def upload_photo(file_bytes: bytes, content_type: str) -> str:
    """Upload child photo to Supabase Storage. Returns public URL."""
    client = await _get_storage_client()
    filename = f"{uuid.uuid4()}.jpg"
    await client.storage.from_(PHOTOS_BUCKET).upload(
        filename,
        file_bytes,
        {"content-type": content_type},
    )
    return await client.storage.from_(PHOTOS_BUCKET).get_public_url(filename)


async def upload_image(image_bytes: bytes, story_id: str, filename: str) -> str:
    """Upload a generated image to Supabase Storage. Returns public URL."""
    client = await _get_storage_client()
    path = f"{story_id}/{filename}"
    await client.storage.from_(IMAGES_BUCKET).upload(
        path,
        image_bytes,
        {"content-type": "image/png"},
    )
    return await client.storage.from_(IMAGES_BUCKET).get_public_url(path)
