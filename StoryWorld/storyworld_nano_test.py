"""
StoryWorld - Nano Banana Pipeline Test v2
Tests the 3-block image prompt system: PHOTO + SCENE + STYLE

The style block is the consistency engine. Every detail that should
stay the same across images MUST be in the style block. The API has
no memory between calls. If it's not in the prompt, it will drift.

Usage:
  python storyworld_nano_test.py --key YOUR_API_KEY
  python storyworld_nano_test.py --key YOUR_API_KEY --photo path/to/child_photo.jpg
  python storyworld_nano_test.py --key YOUR_API_KEY --style watercolor
  python storyworld_nano_test.py --key YOUR_API_KEY --photo photo.jpg --style anime
"""

import argparse
from pathlib import Path
from google import genai
from google.genai import types

# ── CONFIG ─────────────────────────────────────────────
MODEL = "gemini-2.5-flash-image"


# ── STYLE BLOCKS (LOCKED per story) ───────────────────
# These are the constants. Every image in a story gets the SAME block.
# The more specific, the more consistent. Vague = drift.

STYLE_BLOCKS = {
    "photorealism": {
        "name": "Cinematic Photorealism",
        "rendering": "cinematic photorealistic illustration, digital art with photographic quality",
        "palette": "warm earth tones, amber highlights, deep forest greens, cream whites",
        "lighting": "golden hour side lighting from the left, soft diffused shadows, gentle lens flare",
        "atmosphere": "soft depth of field, slight haze in background, dreamy but grounded",
        "camera": "medium shot, eye-level with the child, shallow depth of field, 85mm portrait lens feel",
        "texture": "smooth skin rendering, fabric has visible weave, natural materials look tactile",
    },
    "watercolor": {
        "name": "Storybook Watercolor",
        "rendering": "hand-painted watercolor illustration, children's storybook art, visible brush strokes",
        "palette": "soft pastels, muted pinks and blues, warm yellow accents, white paper showing through",
        "lighting": "flat soft lighting, no harsh shadows, gentle warmth throughout",
        "atmosphere": "whimsical, gentle, cozy, slightly dreamy with soft edges",
        "camera": "slightly elevated view looking down at the child, wide framing, storybook page composition",
        "texture": "watercolor paper grain visible, paint bleeds at edges, soft wet-on-wet blending",
    },
    "anime": {
        "name": "Ghibli-Inspired Anime",
        "rendering": "anime illustration, Studio Ghibli inspired, clean cel-shaded style",
        "palette": "vibrant saturated colors, lush greens, bright sky blues, warm sunset oranges",
        "lighting": "bright and even with dramatic rim lighting on characters, Ghibli cloud lighting",
        "atmosphere": "sense of wonder, vast skies, detailed nature, wind-swept feeling",
        "camera": "cinematic wide shot mixed with character close-ups, dynamic composition",
        "texture": "clean line art, smooth color fills, detailed background painting, soft gradients in sky",
    },
}


def build_style_string(style_key: str, character_outfit: str = None) -> str:
    """Assemble the full locked style block from components."""
    s = STYLE_BLOCKS[style_key]
    parts = [
        f"Art style: {s['rendering']}.",
        f"Color palette: {s['palette']}.",
        f"Lighting: {s['lighting']}.",
        f"Atmosphere: {s['atmosphere']}.",
        f"Camera: {s['camera']}.",
        f"Texture: {s['texture']}.",
    ]
    if character_outfit:
        parts.append(f"The child is wearing: {character_outfit}. This outfit does not change between scenes.")
    parts.append("Maintain exact visual consistency with all other images in this series.")
    return " ".join(parts)


# ── CHARACTER OUTFIT (LOCKED per story) ───────────────
# What the child wears must be specified or the model will
# dress them differently every scene.

DEFAULT_OUTFIT = "a simple cream-colored tunic with a brown leather belt and small brown boots"


# ── SCENE BLOCKS (DYNAMIC - the only thing that changes) ──
# These describe ONLY what is happening and where.
# No character description. No style. No lighting. No palette.
# Just: action + location + key objects.

TEST_SCENES = {
    "fantasy_adventure": [
        {
            "scene": "A child standing at the entrance of a rose garden, discovering a softly glowing stone path that winds toward a distant silver gate",
            "key_objects": "glowing stones, climbing roses, silver gate in background",
        },
        {
            "scene": "A child kneeling in a crystal cave beside a small friendly green dragon, both looking at a glowing crystal between them",
            "key_objects": "green dragon (small, friendly), glowing crystal, cave walls with crystal formations",
        },
        {
            "scene": "A child singing with eyes closed beside a silver gate, flowers blooming from the ground around their feet as the gate swings open",
            "key_objects": "silver gate (opening), blooming flowers, musical notes floating in air",
        },
    ],
    "space_explorer": [
        {
            "scene": "A child stepping out of a small spacecraft onto the surface of a purple moon, looking up at a ringed planet filling the sky",
            "key_objects": "small spacecraft, purple moon surface, ringed planet in sky",
        },
        {
            "scene": "A child floating in a moonbase greenhouse, reaching toward a glowing plant while a small round robot hovers nearby",
            "key_objects": "greenhouse dome, glowing alien plant, round friendly robot",
        },
        {
            "scene": "A child standing at the bridge of a moonbase, pressing a button on a star map console as a nebula swirls outside the window",
            "key_objects": "star map console, panoramic window, colorful nebula outside",
        },
    ],
}


def generate_image(client, scene_block: str, style_block: str, photo_path: str = None) -> bytes:
    """Assemble the 3-block prompt and call the API."""

    contents = []

    # Block 1: REFERENCE PHOTO (locked, attached as image)
    if photo_path:
        photo_bytes = Path(photo_path).read_bytes()
        mime = "image/jpeg" if photo_path.lower().endswith((".jpg", ".jpeg")) else "image/png"
        contents.append(types.Part.from_bytes(data=photo_bytes, mime_type=mime))

    # Assemble: instruction + scene (dynamic) + style (locked)
    if photo_path:
        prompt = (
            f"Using this child's exact likeness and features, generate an illustration. "
            f"Scene: {scene_block} "
            f"Style: {style_block}"
        )
    else:
        prompt = (
            f"Generate an illustration. "
            f"Scene: {scene_block} "
            f"Style: {style_block}"
        )

    contents.append(prompt)

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

    raise RuntimeError("No image returned. Check model access and prompt.")


def main():
    parser = argparse.ArgumentParser(description="StoryWorld Nano Banana pipeline test")
    parser.add_argument("--key", required=True, help="Google AI API key")
    parser.add_argument("--photo", default=None, help="Path to child reference photo")
    parser.add_argument("--style", default="photorealism", choices=STYLE_BLOCKS.keys(), help="Style block to test")
    parser.add_argument("--story", default="fantasy_adventure", choices=TEST_SCENES.keys(), help="Story template")
    parser.add_argument("--outfit", default=DEFAULT_OUTFIT, help="Character outfit description (locked)")
    parser.add_argument("--scenes", type=int, default=3, help="Number of scenes (1-3)")
    args = parser.parse_args()

    client = genai.Client(api_key=args.key)

    # Build the locked style block
    style_block = build_style_string(args.style, args.outfit)
    scenes = TEST_SCENES[args.story][: args.scenes]

    # Output folder named by test params
    out_dir = Path(f"test_{args.style}_{args.story}")
    out_dir.mkdir(exist_ok=True)

    # Save the style block for reference
    (out_dir / "style_block.txt").write_text(style_block)

    print(f"\n{'='*60}")
    print(f"  STORYWORLD PIPELINE TEST")
    print(f"{'='*60}")
    print(f"  Model:   {MODEL}")
    print(f"  Style:   {STYLE_BLOCKS[args.style]['name']}")
    print(f"  Story:   {args.story}")
    print(f"  Photo:   {args.photo or 'none (entity-only mode)'}")
    print(f"  Outfit:  {args.outfit}")
    print(f"  Scenes:  {len(scenes)}")
    print(f"  Output:  ./{out_dir}/")
    print(f"{'='*60}\n")

    print(f"  LOCKED STYLE BLOCK:")
    print(f"  {style_block[:100]}...")
    print()

    for i, scene_data in enumerate(scenes, 1):
        print(f"  [{i}/{len(scenes)}] {scene_data['scene'][:70]}...")
        try:
            img_data = generate_image(client, scene_data["scene"], style_block, args.photo)
            out_path = out_dir / f"scene_{i}.png"
            out_path.write_bytes(img_data)
            print(f"         -> Saved: {out_path}")
        except Exception as e:
            print(f"         -> FAILED: {e}")

    print(f"\n{'='*60}")
    print(f"  CHECK THESE IN ORDER:")
    print(f"{'='*60}")
    print(f"  1. Do all 3 images look like pages from the same book?")
    print(f"  2. Is the color palette consistent across scenes?")
    print(f"  3. Is the lighting direction the same?")
    print(f"  4. Is the child wearing the same outfit?")
    print(f"  5. Does the child's face match the reference photo?")
    print(f"{'='*60}")
    print(f"\n  If something drifts, note WHAT drifted.")
    print(f"  Whatever you add to the style block to fix it")
    print(f"  becomes a permanent template constant.\n")


if __name__ == "__main__":
    main()
