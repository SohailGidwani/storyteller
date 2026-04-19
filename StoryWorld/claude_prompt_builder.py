"""
StoryWorld -- Claude Prompt Builder

This script shows exactly how parent input + config files become a Claude API call.
It reads cognitive_load_config.json and story_type_templates.json, assembles a
complete system prompt, and sends ONE call to Claude that returns the full story JSON.

Pipeline:
  Parent Input (name, age, story_type, adhd)
      |
      v
  cognitive_load_config.json --> age band parameters
  story_type_templates.json --> vocabulary, setting, safety rules
      |
      v
  Assembled System Prompt (tells Claude exactly what to produce)
      |
      v
  Claude API (one call) --> Story JSON (scenes, entities, image prompts)

Usage:
  # Dry run (prints the assembled prompt, no API call):
  python claude_prompt_builder.py --dry-run --name Siena --age 5 --story fantasy_adventure

  # Live call (requires ANTHROPIC_API_KEY env var):
  python claude_prompt_builder.py --name Siena --age 5 --story fantasy_adventure

  # With ADHD modifier:
  python claude_prompt_builder.py --name Siena --age 8 --story space_explorer --adhd
"""

import argparse
import json
import os
from pathlib import Path


# ── CONFIG LOADING ───────────────────────────────────────

def load_configs():
    """Load both config files from the same directory as this script."""
    base = Path(__file__).parent
    with open(base / "cognitive_load_config.json") as f:
        cognitive = json.load(f)
    with open(base / "story_type_templates.json") as f:
        templates = json.load(f)
    return cognitive, templates


def get_age_band(age: int) -> str:
    """Map a child's age to the correct band key."""
    if age <= 5:
        return "4-5"
    elif age <= 8:
        return "6-8"
    else:
        return "9+"


def get_effective_params(cognitive: dict, age_band: str, adhd: bool) -> dict:
    """
    Get the effective parameters for a story, applying ADHD modifier if needed.

    ADHD modifier: content stays at the child's age band (act structure,
    vocabulary, scenes, words/sentence). Delivery parameters shift DOWN
    one band (sentences/block, image breaks, entities, lore, questions).
    """
    base = cognitive["age_bands"][age_band].copy()

    if adhd and age_band != "4-5":
        delivery_band = cognitive["adhd_modifier"]["shift_map"][age_band]
        delivery = cognitive["age_bands"][delivery_band]
        for param in cognitive["adhd_modifier"]["affected_parameters"]:
            base[param] = delivery[param]

    return base


# ── PROMPT ASSEMBLY ──────────────────────────────────────

def build_system_prompt(
    child_name: str,
    age_band: str,
    story_type: str,
    params: dict,
    templates: dict,
    adhd: bool = False,
) -> str:
    """
    Assemble the complete system prompt from config parameters.

    This is the core of the pipeline. Everything Claude needs to generate
    the story is packed into this one prompt. After this call, every child
    interaction is a JSON lookup, not a live API call.
    """
    story = templates["story_types"][story_type]
    safety = "\n".join(f"- {rule}" for rule in templates["safety_rules"])

    adhd_note = ""
    if adhd:
        adhd_note = (
            f"\n\nADHD MODIFIER IS ACTIVE. Content complexity stays at {age_band} level. "
            f"Delivery parameters (sentences per block, image frequency, entity count, "
            f"lore length, question count) have been shifted down one band for reduced "
            f"cognitive load. The values below already reflect this adjustment."
        )

    prompt = f"""You are a children's storybook author. Generate a complete illustrated story as structured JSON.

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
- Vocabulary level: {params["vocabulary"]}

IMAGE PROMPT RULES:
- image_slot prompts describe the SCENE only. What is happening, where, key objects.
- NEVER describe the child's appearance. The photo handles character rendering.
- Write "A child..." not "A five-year-old girl with brown hair..."
- Entity image_prompts describe the object/creature/location. No child, no style info.

SAFETY RULES:
{safety}

OUTPUT FORMAT:
Return valid JSON matching this exact structure:
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
          "word_in_text": "exact words from the text",
          "name": "Display Name",
          "type": "character|location|object|creature",
          "lore": "string ({params["lore_sentences"]} sentence(s))",
          "image_prompt": "string (entity only, no child, no style)",
          "questions": ["string"]
        }}
      ],
      "navigation": {{ "next_scene_id": "scene_2 or null for last" }}
    }}
  ]
}}

Generate the complete story now. Return ONLY the JSON, no markdown fences, no explanation."""

    return prompt


# ── API CALL ─────────────────────────────────────────────

def call_claude(system_prompt: str) -> dict:
    """Send the assembled prompt to Claude and parse the JSON response."""
    try:
        from anthropic import Anthropic
    except ImportError:
        print("ERROR: pip install anthropic")
        raise

    client = Anthropic()  # reads ANTHROPIC_API_KEY from env

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        messages=[{"role": "user", "content": system_prompt}],
    )

    raw = response.content[0].text
    story = json.loads(raw)
    return story


# ── VALIDATION ───────────────────────────────────────────

def validate_story(story: dict, params: dict) -> list:
    """
    Check the generated story against cognitive load constraints.
    Returns a list of warnings (empty = all good).
    """
    warnings = []
    scenes = story.get("scenes", [])

    if len(scenes) != params["scenes"]:
        warnings.append(f"Expected {params['scenes']} scenes, got {len(scenes)}")

    for scene in scenes:
        sid = scene["scene_id"]
        entities = scene.get("clickable_entities", [])
        if len(entities) != params["entities_per_scene"]:
            warnings.append(f"{sid}: expected {params['entities_per_scene']} entities, got {len(entities)}")

        for ent in entities:
            q_count = len(ent.get("questions", []))
            if q_count != params["questions_per_entity"]:
                warnings.append(f"{sid}/{ent['entity_id']}: expected {params['questions_per_entity']} questions, got {q_count}")

        for block in scene.get("text_blocks", []):
            if block["type"] == "text":
                words = block["content"].split()
                # Rough sentence count by period
                sentences = block["content"].count(".") + block["content"].count("!") + block["content"].count("?")
                if sentences > params["sentences_per_block"] + 1:
                    warnings.append(f"{sid}: text block has ~{sentences} sentences, max {params['sentences_per_block']}")

    return warnings


# ── MAIN ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="StoryWorld Claude Prompt Builder")
    parser.add_argument("--name", required=True, help="Child's name")
    parser.add_argument("--age", type=int, required=True, help="Child's age")
    parser.add_argument("--story", required=True, help="Story type key (fantasy_adventure, space_explorer, etc.)")
    parser.add_argument("--adhd", action="store_true", help="Enable ADHD modifier")
    parser.add_argument("--dry-run", action="store_true", help="Print prompt only, no API call")
    parser.add_argument("--output", default=None, help="Save story JSON to this path")
    args = parser.parse_args()

    cognitive, templates = load_configs()
    age_band = get_age_band(args.age)
    params = get_effective_params(cognitive, age_band, args.adhd)

    print(f"\n{'='*60}")
    print(f"  STORYWORLD PROMPT BUILDER")
    print(f"{'='*60}")
    print(f"  Child:      {args.name}, age {args.age}")
    print(f"  Age band:   {age_band}")
    print(f"  Story type: {args.story}")
    print(f"  ADHD:       {'ON' if args.adhd else 'OFF'}")
    print(f"  Acts:       {params['act_structure']} ({len(params['act_names'])} acts)")
    print(f"  Scenes:     {params['scenes']}")
    print(f"  Entities:   {params['entities_per_scene']}/scene")
    print(f"  Delivery:   {params['sentences_per_block']} sent/block, img every {params['image_break_every_n_blocks']} blocks")
    print(f"{'='*60}\n")

    system_prompt = build_system_prompt(
        args.name, age_band, args.story, params, templates, args.adhd
    )

    if args.dry_run:
        print("--- ASSEMBLED SYSTEM PROMPT ---\n")
        print(system_prompt)
        print(f"\n--- END ({len(system_prompt)} chars) ---")
        return

    print("Calling Claude API...")
    story = call_claude(system_prompt)

    # Validate
    warnings = validate_story(story, params)
    if warnings:
        print(f"\n  VALIDATION WARNINGS:")
        for w in warnings:
            print(f"    - {w}")
    else:
        print(f"\n  All constraints validated.")

    # Save
    out_path = args.output or f"story_{args.name.lower()}_{age_band}_{args.story}.json"
    with open(out_path, "w") as f:
        json.dump(story, f, indent=2)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    main()
