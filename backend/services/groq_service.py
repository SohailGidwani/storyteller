"""Story generation via Groq API (fast, OpenAI-compatible)."""

import json
import os
import uuid
from pathlib import Path

from groq import AsyncGroq

_client: AsyncGroq | None = None

def _get_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
    return _client

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

_cognitive: dict | None = None
_templates: dict | None = None

def _load_configs() -> tuple[dict, dict]:
    global _cognitive, _templates
    if _cognitive is None:
        with open(_PROMPTS_DIR / "cognitive_load_config.json") as f:
            _cognitive = json.load(f)
        with open(_PROMPTS_DIR / "story_type_templates.json") as f:
            _templates = json.load(f)
    return _cognitive, _templates

def age_to_band(age: int) -> str:
    if age <= 5:
        return "4-5"
    if age <= 8:
        return "6-8"
    return "9+"

def _get_effective_params(cognitive: dict, age_band: str, adhd: bool) -> dict:
    base = cognitive["age_bands"][age_band].copy()
    if adhd and age_band != "4-5":
        delivery_band = cognitive["adhd_modifier"]["shift_map"][age_band]
        delivery = cognitive["age_bands"][delivery_band]
        for param in cognitive["adhd_modifier"]["affected_parameters"]:
            base[param] = delivery[param]
    return base

def _build_prompt(child_name: str, age_band: str, story_type: str, params: dict, templates: dict, adhd: bool) -> str:
    story = templates["story_types"][story_type]
    safety = "\n".join(f"- {rule}" for rule in templates["safety_rules"])
    adhd_note = ""
    if adhd:
        adhd_note = (
            f"\n\nADHD MODIFIER ACTIVE. Content stays at {age_band} level. "
            "Delivery parameters already shifted down one band in values below."
        )

    return f"""You are a children's storybook author. Generate a complete illustrated story as structured JSON.

CHILD: {child_name}, age band {age_band}
STORY TYPE: {story["label"]}
SETTING: {story["setting"]}
TONE: {story["tone"]}
VOCABULARY POOL: {", ".join(story["vocabulary"])}{adhd_note}

STRUCTURE REQUIREMENTS:
- Act structure: {params["act_structure"]} ({", ".join(params["act_names"])})
- Total scenes: {params["scenes"]}
- Sentences per text block: exactly {params["sentences_per_block"]}
- Words per sentence: target {params["words_per_sentence"]} (max {params["words_per_sentence"] + 2})
- Image slot: insert one image_slot every {params["image_break_every_n_blocks"]} text block(s)
- Entities per scene: exactly {params["entities_per_scene"]}
- Lore length: {params["lore_sentences"]} sentence(s) per entity
- Questions per entity: {params["questions_per_entity"]}
- Flesch-Kincaid target: grade {params["flesch_kincaid_target"]}

IMAGE PROMPT RULES:
- image_slot prompts describe the SCENE only. What is happening, where, key objects.
- NEVER describe the child's appearance. Write "A child..." not "A girl with brown hair..."
- Entity image_prompts describe the object/creature/location only. No child, no style info.

SAFETY RULES:
{safety}

OUTPUT FORMAT — return ONLY valid JSON, no markdown fences, no explanation:
{{
  "title": "string",
  "child_name": "{child_name}",
  "age_band": "{age_band}",
  "act_structure": "{params["act_structure"]}",
  "story_type": "{story_type}",
  "scenes": [
    {{
      "scene_id": "scene_1",
      "act": 1,
      "act_name": "{params["act_names"][0]}",
      "title": "string",
      "text_blocks": [
        {{ "type": "text", "content": "string" }},
        {{ "type": "image_slot", "prompt": "string", "alt": "string" }}
      ],
      "clickable_entities": [
        {{
          "entity_id": "ent_name_1",
          "word_in_text": "exact phrase from the preceding text block",
          "name": "Display Name",
          "type": "character|location|object|creature",
          "lore": "string",
          "image_prompt": "string",
          "questions": ["string"]
        }}
      ],
      "navigation": {{ "next_scene_id": "scene_2 or null for last" }}
    }}
  ]
}}

Generate the complete story now."""


def _load_demo_fallback(photo_url: str) -> dict:
    with open(_FIXTURES_DIR / "demo_story.json") as f:
        story = json.load(f)
    story["story_id"] = str(uuid.uuid4())
    story["status"] = "complete"
    story["photo_url"] = photo_url
    return story


async def generate_story(child_name: str, age: int, photo_url: str, story_type: str, adhd: bool = False) -> dict:
    """Generate story via Groq. Falls back to demo_story.json on any failure."""
    cognitive, templates = _load_configs()
    age_band = age_to_band(age)
    params = _get_effective_params(cognitive, age_band, adhd)
    prompt = _build_prompt(child_name, age_band, story_type, params, templates, adhd)

    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8192,
            temperature=0.7,
        )
        raw = response.choices[0].message.content or ""
        # Strip accidental markdown fences
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        story = json.loads(raw.strip())
    except Exception:
        story = _load_demo_fallback(photo_url)
        return story

    story["story_id"] = str(uuid.uuid4())
    story["status"] = "complete"
    story["photo_url"] = photo_url
    return story
