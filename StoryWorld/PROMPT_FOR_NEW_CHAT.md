# StoryWorld -- Context Prompt

Copy everything below this line into a new Claude chat to give it full project context.

---

You are helping me build StoryWorld at a hackathon today. Here is the full project scope.

## What It Is

StoryWorld is an AI-powered personalized children's storybook app for iPad. A parent uploads their child's photo, picks an age and story type, taps Generate, and hands the iPad to the child. The app generates a complete illustrated story where the child is the hero, with every image and every word calibrated to their reading level.

**Hackathon theme: Social Impact.** The angle is literacy access (age-calibrated reading), representation (child sees themselves as the hero), and inclusive design (ADHD modifier adjusts delivery without dumbing down content).

## Architecture

**Backend: FastAPI (Python).** Two external API dependencies:

1. Claude API (Anthropic) -- one call generates the entire story as structured JSON. System prompt is assembled from pre-built templates (age band + act structure + story type vocab). After generation, every child interaction is a JSON lookup, not a live API call.

2. Image Gen API (Nano Banana / Gemini 2.5 Flash Image) -- generates illustrations. Each call is independent with no memory. Model name: `gemini-2.5-flash-image`. Library: `google-genai`.

**Frontend: Plain HTML/CSS/JS** served to iPad via Safari (or SwiftUI if time allows). Reader view shows one scene at a time. Side panel slides from right on entity tap (lore, entity image, curiosity questions). No blocking spinner -- text renders first, images fill in progressively.

## Three-Block Image Prompt System

Every image prompt is assembled from three blocks:

- **REFERENCE PHOTO (locked):** child's photo, attached every call. Not for entity-only images.
- **SCENE BLOCK (dynamic):** the only thing that changes. Claude writes scene descriptions, NOT character descriptions. "A child discovering a glowing path" -- not "a five-year-old girl with brown hair." The photo does the character work.
- **STYLE BLOCK (locked):** identical string for every image in a story. Locks down: rendering style, color palette, lighting, atmosphere, camera, texture, character outfit. Attached by backend.

Three image types: hero portrait (once, first, anchor), scene images (multiple, hardest -- child must stay consistent), entity images (objects/locations, no photo needed).

## Cognitive Load -- Three Age Bands

| Parameter | Age 4-5 | Age 6-8 | Age 9+ |
|-----------|---------|---------|--------|
| Act structure | 3-act | 5-act | 7-act |
| Scenes | 3 | 5 | 7 |
| Sentences/block | 2 | 4 | 6 |
| Words/sentence | 8 | 12 | 16 |
| Image break | every block | every 2 | every 3 |
| Entities/scene | 2 | 4 | 5 |
| Lore length | 1 sentence | 3 sentences | 5 sentences |
| Questions/entity | 1 | 3 | 4 |
| Vocabulary | simple | compound | nuance, abstract |
| Flesch-Kincaid | grade 1 | grade 3 | grade 5 |

ADHD modifier: content stays at child's age level, delivery parameters shift down one band.

## Story JSON Contract

Claude returns JSON with: title, child_name, age_band, act_structure, story_type, scenes[]. Each scene has: scene_id, act, act_name, title, text_blocks[] (interleaved text + image_slot), clickable_entities[] (entity_id, word_in_text, name, type, lore, image_prompt, questions), navigation.

Image prompts in the JSON describe the scene only. Backend attaches photo + style block before calling the image API.

## Fallback Strategy

Pre-generate one complete story (JSON + all images) before the demo. If any API fails, backend serves the pre-baked version. Frontend can't tell the difference. If everything fails, offline bundle works with zero internet.

## Key Decisions Already Made

- Templates are hardcoded JSON, not a database
- Stories live in memory (session only), Supabase is optional
- Image gen model is TBD pending testing (start with Nano Banana, fall back to DALL-E)
- Default art style: cinematic photorealism
- Demo target: Siena, age 5, fantasy_adventure
- Frontend framework: plain HTML/CSS/JS (SwiftUI stretch goal)

## What I Need Help With

[FILL IN YOUR SPECIFIC REQUEST HERE]

## Reference Files

I have the following files available:
- PROJECT_SCOPE.md -- full scope document
- example_story_age4-5.json -- complete example of Claude's JSON output
- storyworld_nano_test.py -- image pipeline test script with style blocks
- Siena/ -- 3 reference photos (portrait-img.png is best)
- StoryWorld Architecture Reference v2.html -- full architecture with SVG diagrams
- StoryWorld Build Reference.html -- 10-slide pitch deck
