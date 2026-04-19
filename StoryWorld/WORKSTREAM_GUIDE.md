# StoryWorld -- Parallel Workstream Guide

Three people can work simultaneously without stepping on each other. Each workstream owns specific files and communicates through one shared contract: the Story JSON schema.


## The Integration Point

Everything flows through the Story JSON. Claude produces it, the image pipeline consumes it, the frontend renders it. If your workstream reads or writes JSON, the schema in `example_story_age4-5.json` is your contract. Do not change the schema without telling the other two workstreams.


## Workstream A: Story Generation (Backend)

**Owner:** Arash
**What you build:** The FastAPI endpoint that takes parent input and returns a complete Story JSON.

**Files you own:**
- `claude_prompt_builder.py` -- assembles the Claude system prompt from configs
- `cognitive_load_config.json` -- age band parameters (shared, read-only for other workstreams)
- `story_type_templates.json` -- story types, vocabulary, safety rules, style blocks (shared, read-only for other workstreams)

**What you produce:** A `/generate` endpoint that accepts `{name, age, story_type, adhd}` and returns Story JSON.

**How to start:**
1. Run `python claude_prompt_builder.py --dry-run --name Siena --age 5 --story fantasy_adventure` to see the assembled prompt.
2. Wrap the `build_system_prompt()` and `call_claude()` functions in a FastAPI route.
3. Add `validate_story()` as a post-generation check before returning.
4. Test with all three age bands. Compare output against the example JSONs.

**Your interfaces:**
- IN: Parent form data (name, age, story_type, adhd toggle)
- OUT: Story JSON (same schema as example files)
- The image pipeline reads your JSON output. The frontend reads your JSON output. Neither modifies it.

**ADHD modifier logic** is already in `claude_prompt_builder.py` (`get_effective_params`). It reads from `cognitive_load_config.json` and adjusts delivery parameters automatically.

**Validation** catches constraint violations (wrong scene count, too many entities, etc.) before the JSON reaches the frontend.


## Workstream B: Image Pipeline (Backend)

**Owner:** Arash (or teammate)
**What you build:** The system that reads image_slot prompts and entity image_prompts from Story JSON, assembles 3-block prompts, and calls the Gemini API.

**Files you own:**
- `image_pipeline.py` -- takes a Story JSON, produces all images
- `storyworld_nano_test.py` -- standalone style block testing (already works)

**What you produce:** A folder of images named by scene and slot, plus a manifest.

**How to start:**
1. Run `python image_pipeline.py --dry-run --story example_story_age4-5.json --photo Siena/portrait-img.png` to see all assembled prompts.
2. Enable billing on Google AI API key.
3. Run live: `python image_pipeline.py --key YOUR_KEY --story example_story_age4-5.json --photo Siena/portrait-img.png`
4. Check the 5-point consistency checklist printed at the end.

**Your interfaces:**
- IN: Story JSON (reads `image_slot.prompt` and `entity.image_prompt` fields)
- IN: Child reference photo (from parent upload)
- IN: Style block (from `story_type_templates.json`, key determined by story type)
- OUT: Image files named `{scene_id}_img{N}.png` and `{scene_id}_{entity_id}.png`
- OUT: `manifest.json` linking each image to its source prompt

**The 3-block system:**
1. PHOTO (locked): child's reference photo, attached as image data. Omitted for entity images.
2. SCENE (dynamic): from the Story JSON's `image_slot.prompt` or `entity.image_prompt`. This is the ONLY variable.
3. STYLE (locked): built from `story_type_templates.json`. Identical for every image in a story.

**Three image types:**
- Hero portrait: photo YES, generated first, anchors appearance
- Scene images: photo YES, must match hero portrait
- Entity images: photo NO, objects/locations/creatures only

**Consistency depends on the style block.** If something drifts (outfit changes, lighting shifts, palette breaks), the fix goes into the style block, not the scene prompt.


## Workstream C: Frontend Reader (Frontend)

**Owner:** Sylvan
**What you build:** The iPad reader UI that renders a Story JSON as a storybook.

**Files you own:** Your HTML/CSS/JS files (create in a `frontend/` subfolder)

**What you produce:** A reader that shows one scene at a time with text, images, and an entity side panel.

**How to start:**
1. Read `example_story_age4-5.json` to understand the data shape.
2. Compare with `example_story_age6-8.json` and `example_story_age9+.json` to see how the same schema scales.
3. Build a static reader that loads any example JSON and renders it.
4. Add the entity side panel (slides from right on entity tap).

**Your interfaces:**
- IN: Story JSON (fetched from backend `/generate` endpoint, or loaded locally from example files)
- IN: Image files (URLs from backend, or local paths during development)
- OUT: Rendered storybook in iPad Safari

**Reader layout:**
- Scene title at top
- Text blocks render as paragraphs
- Image slots render as image elements (show placeholder until image loads)
- Clickable entities: highlight `word_in_text` in the prose. On tap, slide panel from right showing: entity name, lore, entity image, curiosity questions.
- Navigation: next/previous scene buttons (read from `navigation.next_scene_id`)

**Progressive loading:**
- Text renders immediately (no spinner)
- Images fill in as they arrive from the pipeline
- Entity images load when the side panel opens (lazy)

**Age band differences visible in the JSON:**
- 4-5: 3 scenes, 2 entities/scene, short text blocks, image every block
- 6-8: 5 scenes, 4 entities/scene, longer text blocks, image every 2 blocks
- 9+: 7 scenes, 5 entities/scene, longest text blocks, image every 3 blocks
- You do not need to handle these differences in code. The JSON already has the right number of everything. Just render what the JSON contains.


## Integration Contract

All three workstreams depend on the Story JSON schema. Here is what each workstream can assume:

**Schema guarantees:**
- `scenes` is an ordered array. Render in order.
- Every scene has `text_blocks` (array of text and image_slot objects, interleaved).
- Every scene has `clickable_entities` (array, count varies by age band).
- Every entity has `word_in_text` (exact string to highlight in the prose).
- `navigation.next_scene_id` is a string or null (null = last scene).
- Image filenames follow the pattern in `image_pipeline.py`: `{scene_id}_img{N}.png` for scenes, `{scene_id}_{entity_id}.png` for entities, `hero_portrait.png` for the portrait.

**What not to change without coordination:**
- The `text_blocks` interleaving pattern (text, image_slot, text, image_slot)
- The `clickable_entities` field names (`word_in_text`, `lore`, `image_prompt`, `questions`)
- The `navigation` structure
- Image naming convention


## File Inventory

```
StoryWorld/
  cognitive_load_config.json   -- age band parameters (Workstream A owns, all read)
  story_type_templates.json    -- story types + style blocks (Workstream A owns, B reads)
  claude_prompt_builder.py     -- Claude prompt assembly + validation (Workstream A)
  image_pipeline.py            -- 3-block image generation (Workstream B)
  storyworld_nano_test.py      -- standalone image testing (Workstream B)
  example_story_age4-5.json    -- reference JSON, 3-act (all read)
  example_story_age6-8.json    -- reference JSON, 5-act (all read)
  example_story_age9+.json     -- reference JSON, 7-act (all read)
  PROJECT_SCOPE.md             -- full project scope (reference)
  PROMPT_FOR_NEW_CHAT.md       -- context prompt for new Claude chats (reference)
  WORKSTREAM_GUIDE.md          -- this file
  Siena/                       -- reference photos (Workstream B)
    portrait-img.png           -- best reference photo
```


## Pre-Demo Checklist

Before the demo, one complete story must be pre-baked (JSON + all images saved locally). This is the fallback. If any API fails during the demo, the frontend serves the pre-baked version. The frontend cannot tell the difference.

1. Run `claude_prompt_builder.py` live to generate a story JSON for Siena, age 5, fantasy_adventure.
2. Run `image_pipeline.py` live with Siena's photo to generate all images.
3. Save both the JSON and the images folder as the fallback bundle.
4. Test the frontend with the fallback bundle (no API calls).
5. If the fallback works, the demo is safe regardless of API status.
