"""
StoryWorld -- Image Pipeline

This script shows exactly how a story JSON becomes a set of illustrated images.
It reads a generated story JSON, assembles 3-block prompts for each image slot,
and calls the Gemini image gen API.

Pipeline:
  Story JSON (from Claude)
      |
      v
  For each image_slot in each scene:
      |
      +-- Block 1: PHOTO (locked, child's reference photo)
      +-- Block 2: SCENE (dynamic, from image_slot.prompt)
      +-- Block 3: STYLE (locked, from story_type_templates.json)
      |
      v
  Assembled prompt --> Gemini API --> saved .png

Three image types with different assembly:

  1. HERO PORTRAIT (first image, anchor)
     Photo: YES | Scene: "A portrait of a child standing confidently..." | Style: YES

  2. SCENE IMAGES (multiple per story, hardest)
     Photo: YES | Scene: from story JSON image_slot.prompt | Style: YES

  3. ENTITY IMAGES (objects, locations, creatures)
     Photo: NO  | Scene: from entity.image_prompt | Style: YES (consistency only)

Usage:
  # Generate all images for a story:
  python image_pipeline.py --key YOUR_GOOGLE_KEY --story example_story_age4-5.json --photo Siena/portrait-img.png

  # Entity images only (no photo needed):
  python image_pipeline.py --key YOUR_GOOGLE_KEY --story example_story_age4-5.json --entities-only

  # Custom style:
  python image_pipeline.py --key YOUR_GOOGLE_KEY --story example_story_age4-5.json --photo Siena/portrait-img.png --style watercolor

  # Dry run (print assembled prompts, no API calls):
  python image_pipeline.py --dry-run --story example_story_age4-5.json --photo Siena/portrait-img.png
"""

import argparse
import json
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None


# ── STYLE BLOCK ASSEMBLY ────────────────────────────────

def load_style_blocks():
    """Load style blocks from story_type_templates.json."""
    base = Path(__file__).parent
    with open(base / "story_type_templates.json") as f:
        templates = json.load(f)
    return templates["style_blocks"]


def build_style_string(style_blocks: dict, style_key: str, outfit: str = None) -> str:
    """
    Assemble the locked style block string.

    This string is IDENTICAL for every image in a story. It locks down:
    rendering style, color palette, lighting, atmosphere, camera, texture.
    Plus the character outfit (if provided) to prevent wardrobe drift.
    """
    s = style_blocks[style_key]
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


# ── PROMPT ASSEMBLY ──────────────────────────────────────

def assemble_scene_prompt(scene_description: str, style_string: str, has_photo: bool) -> str:
    """
    Assemble the text portion of a scene image prompt.

    If a photo is attached, the instruction references it.
    The photo itself is attached as a separate Part (see generate_image).
    """
    if has_photo:
        return (
            f"Using this child's exact likeness and features, generate an illustration. "
            f"Scene: {scene_description} "
            f"Style: {style_string}"
        )
    else:
        return (
            f"Generate an illustration. "
            f"Scene: {scene_description} "
            f"Style: {style_string}"
        )


def assemble_entity_prompt(entity_description: str, style_string: str) -> str:
    """
    Assemble an entity image prompt. No photo needed.
    Entities are objects, locations, creatures -- not the child.
    """
    return (
        f"Generate an illustration of this object/creature/location. "
        f"Subject: {entity_description} "
        f"Style: {style_string}"
    )


def assemble_hero_portrait_prompt(child_name: str, style_string: str) -> str:
    """
    Assemble the hero portrait prompt. This is generated FIRST and anchors
    the child's appearance for the rest of the story.
    """
    return (
        f"Using this child's exact likeness and features, generate a portrait illustration. "
        f"Scene: A child standing confidently in a magical setting, looking directly at the viewer with a warm smile. "
        f"This is {child_name}, the hero of this story. "
        f"Style: {style_string}"
    )


# ── API CALLS ────────────────────────────────────────────

MODEL = "gemini-2.5-flash-image"


def generate_image(client, prompt_text: str, photo_path: str = None) -> bytes:
    """
    Call Gemini image gen API with assembled prompt.

    If photo_path is provided, it's attached as Block 1 (reference photo).
    The prompt_text already contains Block 2 (scene) + Block 3 (style).
    """
    contents = []

    # Block 1: Reference photo (if needed)
    if photo_path:
        photo_bytes = Path(photo_path).read_bytes()
        mime = "image/jpeg" if photo_path.lower().endswith((".jpg", ".jpeg")) else "image/png"
        contents.append(types.Part.from_bytes(data=photo_bytes, mime_type=mime))

    # Block 2 + 3: Scene + Style (already assembled in prompt_text)
    contents.append(prompt_text)

    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            return part.inline_data.data

    raise RuntimeError("No image returned. Check model access and billing.")


# ── STORY IMAGE EXTRACTION ───────────────────────────────

def extract_image_jobs(story: dict) -> list:
    """
    Walk the story JSON and extract every image that needs generating.

    Returns a list of dicts:
      { "type": "hero"|"scene"|"entity",
        "scene_id": str,
        "prompt": str (raw, from JSON),
        "alt": str,
        "needs_photo": bool,
        "filename": str }
    """
    jobs = []
    child_name = story.get("child_name", "Child")

    # Job 0: Hero portrait (always first)
    jobs.append({
        "type": "hero",
        "scene_id": "portrait",
        "prompt": f"A portrait of {child_name} standing confidently in a magical setting, looking directly at the viewer with a warm smile",
        "alt": f"{child_name} hero portrait",
        "needs_photo": True,
        "filename": "hero_portrait.png",
    })

    # Scene images and entity images
    for scene in story.get("scenes", []):
        sid = scene["scene_id"]
        img_count = 0

        for block in scene.get("text_blocks", []):
            if block["type"] == "image_slot":
                img_count += 1
                jobs.append({
                    "type": "scene",
                    "scene_id": sid,
                    "prompt": block["prompt"],
                    "alt": block.get("alt", ""),
                    "needs_photo": True,
                    "filename": f"{sid}_img{img_count}.png",
                })

        for ent in scene.get("clickable_entities", []):
            jobs.append({
                "type": "entity",
                "scene_id": sid,
                "prompt": ent["image_prompt"],
                "alt": ent["name"],
                "needs_photo": False,
                "filename": f"{sid}_{ent['entity_id']}.png",
            })

    return jobs


# ── MAIN ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="StoryWorld Image Pipeline")
    parser.add_argument("--key", default=None, help="Google AI API key (or set GOOGLE_AI_API_KEY env)")
    parser.add_argument("--story", required=True, help="Path to story JSON file")
    parser.add_argument("--photo", default=None, help="Path to child reference photo")
    parser.add_argument("--style", default="photorealism", help="Style block key")
    parser.add_argument("--outfit", default=None, help="Character outfit (overrides story type default)")
    parser.add_argument("--entities-only", action="store_true", help="Only generate entity images (no photo needed)")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts, no API calls")
    parser.add_argument("--output", default=None, help="Output directory (default: images_{story_title})")
    args = parser.parse_args()

    # Load story
    with open(args.story) as f:
        story = json.load(f)

    # Load style blocks and build the locked string
    style_blocks = load_style_blocks()

    # Get outfit from story type template if not overridden
    outfit = args.outfit
    if not outfit:
        base = Path(__file__).parent
        with open(base / "story_type_templates.json") as f:
            templates = json.load(f)
        story_type = story.get("story_type", "fantasy_adventure")
        outfit = templates["story_types"].get(story_type, {}).get("default_outfit")

    style_string = build_style_string(style_blocks, args.style, outfit)

    # Extract all image jobs from the story JSON
    jobs = extract_image_jobs(story)
    if args.entities_only:
        jobs = [j for j in jobs if j["type"] == "entity"]

    # Output directory
    title_slug = story.get("title", "story").lower().replace(" ", "_")[:30]
    out_dir = Path(args.output or f"images_{title_slug}")
    out_dir.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  STORYWORLD IMAGE PIPELINE")
    print(f"{'='*60}")
    print(f"  Story:    {story.get('title', 'Unknown')}")
    print(f"  Style:    {args.style}")
    print(f"  Photo:    {args.photo or 'none'}")
    print(f"  Outfit:   {outfit or 'none'}")
    print(f"  Jobs:     {len(jobs)} images")
    print(f"  Output:   ./{out_dir}/")
    print(f"{'='*60}")
    print(f"\n  LOCKED STYLE BLOCK ({len(style_string)} chars):")
    print(f"  {style_string[:100]}...\n")

    # Process each image job
    client = None
    if not args.dry_run:
        if not genai:
            print("ERROR: pip install google-genai")
            return
        api_key = args.key or os.environ.get("GOOGLE_AI_API_KEY")
        if not api_key:
            print("ERROR: provide --key or set GOOGLE_AI_API_KEY")
            return
        client = genai.Client(api_key=api_key)

    for i, job in enumerate(jobs, 1):
        print(f"  [{i}/{len(jobs)}] {job['type'].upper():8s} {job['filename']}")

        # Assemble the prompt based on image type
        if job["type"] == "hero":
            prompt_text = assemble_hero_portrait_prompt(
                story.get("child_name", "Child"), style_string
            )
        elif job["type"] == "scene":
            prompt_text = assemble_scene_prompt(
                job["prompt"], style_string, has_photo=bool(args.photo)
            )
        elif job["type"] == "entity":
            prompt_text = assemble_entity_prompt(job["prompt"], style_string)

        if args.dry_run:
            print(f"           Photo: {'YES' if job['needs_photo'] else 'NO'}")
            print(f"           Prompt: {prompt_text[:120]}...")
            print()
            continue

        try:
            photo = args.photo if job["needs_photo"] else None
            img_data = generate_image(client, prompt_text, photo)
            out_path = out_dir / job["filename"]
            out_path.write_bytes(img_data)
            print(f"           -> Saved: {out_path}")
        except Exception as e:
            print(f"           -> FAILED: {e}")

    # Save job manifest for debugging
    manifest = {
        "story_title": story.get("title"),
        "style": args.style,
        "style_string": style_string,
        "outfit": outfit,
        "total_jobs": len(jobs),
        "jobs": [{"type": j["type"], "filename": j["filename"], "prompt": j["prompt"]} for j in jobs],
    }
    manifest_path = out_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\n  Manifest: {manifest_path}")

    print(f"\n{'='*60}")
    print(f"  CONSISTENCY CHECK:")
    print(f"{'='*60}")
    print(f"  1. Does hero portrait anchor the child's look?")
    print(f"  2. Do scene images match the hero portrait?")
    print(f"  3. Is the outfit the same in every scene?")
    print(f"  4. Are colors and lighting consistent?")
    print(f"  5. Do entity images match the story's art style?")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import os
    main()
