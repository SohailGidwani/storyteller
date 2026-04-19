# StoryWorld -- Full Project Scope

## What It Is

StoryWorld is an AI-powered personalized children's storybook app. A parent uploads a photo of their child, picks an age and story type, and the app generates a complete illustrated story where the child is the hero. The child sees themselves in every scene. Every word, every image, every interaction is calibrated to the child's reading level.

## Social Impact Angle (Hackathon Theme)

Not every kid sees themselves in the books available to them. Not every kid reads at their grade level. Not every kid can sit through the same length story. StoryWorld adapts to all three: representation (the child is literally the hero), literacy access (age-calibrated reading levels with Flesch-Kincaid targeting), and inclusive design (ADHD modifier that adjusts delivery without dumbing down content).

## The Demo

iPad in hand. Parent fills out one form (photo, name, age). Taps Generate. Hands iPad to the child. The child reads a story starring themselves, taps highlighted words to explore a knowledge graph (lore, images, curiosity questions), and sees AI-generated illustrations of themselves in every scene.

Target child for demo: Siena, age 5.

---

## Architecture

### Two API Dependencies

1. **Claude API (Anthropic)** -- generates the story as structured JSON from a templated system prompt. One call per story. Every child interaction after generation is a JSON lookup, not a live API call.

2. **Image Gen API (Nano Banana / Gemini)** -- generates illustrations from a templated prompt. Each call is independent, no memory between calls. Consistency comes from what you pack into each prompt.

### The Pipeline

```
Parent Input (photo + name + age)
    |
    v
Backend (FastAPI)
    |-- Selects age band template (3 bands: 4-5, 6-8, 9+)
    |-- Selects story type template (fantasy, space, animal, superhero, royal)
    |-- Assembles system prompt from templates
    |-- Sends ONE call to Claude API
    |
    v
Claude Returns Story JSON
    |-- Scenes with text blocks and image_slot prompts
    |-- Clickable entities (knowledge graph) with lore, image prompts, questions
    |
    v
Image Pipeline (backend assembles, calls image API)
    |-- For each image_slot: PHOTO (locked) + SCENE (from Claude) + STYLE (locked)
    |-- For each entity: SCENE (from Claude) + STYLE (locked), no photo needed
    |-- Images fill in progressively as they return
    |
    v
Frontend renders the storybook on iPad
```

### Three-Block Image Prompt System

Every image prompt is assembled from three blocks:

- **Block 1: Reference Photo (LOCKED)** -- the child's photo, attached to every scene call. Never changes. Not needed for entity-only images (objects, locations).

- **Block 2: Scene Block (DYNAMIC)** -- describes what is happening in the scene. This is the ONLY thing that changes between image calls. Claude writes these as part of the story JSON. Scene descriptions only, not character descriptions. "A child discovering a glowing path beside a rose garden" -- not "a five-year-old girl with brown curly hair." The photo does the character work.

- **Block 3: Style Block (LOCKED)** -- identical string for every image in a story. Attached by the backend to maintain consistent style, setting, and context across all images. Locks down: rendering style, color palette, lighting direction, atmosphere, camera framing, texture, and character outfit.

### Three Image Types

| Type | When | Needs Photo? | Challenge |
|------|------|-------------|-----------|
| Hero portrait | Once, first | Yes | This IS the anchor. Photo in, styled character out. |
| Scene images | Multiple per story | Yes | Hardest. Child must look the same across every scene. |
| Entity images | Per entity | No | Easier. Objects and locations only. Style consistency only. |

### Consistency Strategy

The API has no memory between calls. Consistency is NOT from session state. It comes from:
- Style block: identical word-for-word for every image
- Hero portrait: generated first, anchors the child's appearance
- Character outfit: specified in style block, never changes
- Each call is independent -- if it's not in the prompt, it will drift

---

## Cognitive Load System

### Three Age Bands

| Parameter | Age 4-5 | Age 6-8 | Age 9+ |
|-----------|---------|---------|--------|
| Act structure | 3-act | 5-act | 7-act (hero's journey) |
| Scenes | 3 | 5 | 7 |
| Sentences per block | 2 | 4 | 6 |
| Words per sentence | 8 | 12 | 16 |
| Image break | every block | every 2 blocks | every 3 blocks |
| Entities per scene | 2 | 4 | 5 |
| Lore length | 1 sentence | 3 sentences | 5 sentences |
| Questions per entity | 1 | 3 | 4 |
| Vocabulary | simple, concrete | compound ok | nuance, abstract |
| Flesch-Kincaid target | grade 1 | grade 3 | grade 5 |

### ADHD Modifier

Parent toggle. Content stays at the child's age level, but delivery parameters shift down one band. Example: a 9-year-old with the modifier keeps 7-act structure, nuanced vocabulary, 16 words/sentence, and 7 scenes. But sentences per block drops to 4, image breaks come every 2 blocks, entities per scene drops to 4, lore shortens to 3 sentences, and questions drop to 3.

### Act Structures

- **Age 4-5 (3-act):** The World, The Problem, The Fix
- **Age 6-8 (5-act):** Ordinary World, The Call, Rising Challenge, The Climax, Return
- **Age 9+ (7-act):** Ordinary World, Call to Adventure, Crossing the Threshold, Trials and Allies, The Ordeal, The Reward, The Return

---

## Story JSON Schema

### Top Level

| Field | Type | Description |
|-------|------|-------------|
| title | string | Story title Claude writes |
| child_name | string | From parent input |
| age_band | string | "4-5", "6-8", "9+" |
| act_structure | string | "3_act", "5_act", "7_act" |
| story_type | string | fantasy_adventure, space_explorer, animal_quest, superhero_mission, royal_tale |
| scenes | array | Scene objects, ordered |

### Scene Object

| Field | Type | Description |
|-------|------|-------------|
| scene_id | string | scene_1, scene_2, ... |
| act | number | Which act |
| act_name | string | e.g. "The World" |
| title | string | Scene title |
| text_blocks | array | Text and image_slot objects, interleaved |
| clickable_entities | array | Entity objects (knowledge graph) |
| navigation | object | { next_scene_id: string or null } |

### Text Block Types

- `type: "text"` -- prose the child reads. `content` field.
- `type: "image_slot"` -- where an illustration goes. `prompt` field (scene only, no character, no style) + `alt` field.

### Entity Object

| Field | Type | Description |
|-------|------|-------------|
| entity_id | string | ent_{name}_{number} |
| word_in_text | string | Exact word(s) highlighted in prose |
| name | string | Display name in side panel |
| type | enum | character, location, object, creature |
| lore | string | Short description, length set by age band |
| image_prompt | string | Entity illustration description. No style, no child. |
| questions | array | Curiosity prompts. Count set by age band. |

---

## Tech Stack

### Backend
- **Python / FastAPI**
- Claude API via `anthropic` Python SDK
- Image gen via `google-genai` Python SDK (Nano Banana / Gemini)
- Templates as hardcoded JSON (age bands, story types, style blocks)
- Stories in memory (session only). Supabase optional for persistence.

### Frontend
- **Plain HTML/CSS/JS** (recommended for hackathon)
- OR SwiftUI (better UX, higher risk, requires Xcode)
- iPad-optimized layout
- Reader view: scene text + images, one scene at a time
- Side panel: slides from right on entity tap (lore, image, questions)
- No blocking spinner: text renders first, images fill in progressively

### Image Gen API
- **Primary: Nano Banana (Gemini 2.5 Flash Image)** -- ~$0.04/image, API via google-genai
- **Fallback: DALL-E** -- per image, well documented, weaker image-to-image
- **Later: ComfyUI on 4090** -- best consistency (IP-Adapter, ControlNet), requires home server setup
- Model name: `gemini-2.5-flash-image`
- Requires billing enabled on Google AI Studio API key

### Hosting
- Backend: run locally on laptop, or deploy to Railway/Render
- Frontend: serve from backend, or static file on Netlify
- For demo: everything local on the same machine, iPad connects over local network

---

## Fallback Strategy

Plan the demo as if both APIs will be down and WiFi will drop.

### Pre-generate before demo:
- One complete story JSON (run Claude call, save output)
- All images for that story (run image pipeline, save files)
- Hero portrait with Siena's photo
- Offline bundle: JSON + all images packaged for direct frontend load

### Failure cascade:
1. Claude down? Backend serves pre-baked JSON. Frontend can't tell.
2. Image gen down? Story renders text-only, or loads pre-generated images.
3. Both down? Full pre-baked mode. Everything local.
4. Backend crashes? Frontend loads local JSON directly.
5. WiFi drops? Offline bundle. Everything local. Demo still works.
6. Image gen produces bad output? Swap in pre-gen images for that scene.

---

## Style Blocks (Pre-Built)

### Cinematic Photorealism (default)
```
Art style: cinematic photorealistic illustration, digital art with photographic quality.
Color palette: warm earth tones, amber highlights, deep forest greens, cream whites.
Lighting: golden hour side lighting from the left, soft diffused shadows, gentle lens flare.
Atmosphere: soft depth of field, slight haze in background, dreamy but grounded.
Camera: medium shot, eye-level with the child, shallow depth of field, 85mm portrait lens feel.
Texture: smooth skin rendering, fabric has visible weave, natural materials look tactile.
The child is wearing: [outfit]. This outfit does not change between scenes.
Maintain exact visual consistency with all other images in this series.
```

### Storybook Watercolor
```
Art style: hand-painted watercolor illustration, children's storybook art, visible brush strokes.
Color palette: soft pastels, muted pinks and blues, warm yellow accents, white paper showing through.
Lighting: flat soft lighting, no harsh shadows, gentle warmth throughout.
Atmosphere: whimsical, gentle, cozy, slightly dreamy with soft edges.
Camera: slightly elevated view looking down at the child, wide framing, storybook page composition.
Texture: watercolor paper grain visible, paint bleeds at edges, soft wet-on-wet blending.
```

### Ghibli-Inspired Anime
```
Art style: anime illustration, Studio Ghibli inspired, clean cel-shaded style.
Color palette: vibrant saturated colors, lush greens, bright sky blues, warm sunset oranges.
Lighting: bright and even with dramatic rim lighting on characters, Ghibli cloud lighting.
Atmosphere: sense of wonder, vast skies, detailed nature, wind-swept feeling.
Camera: cinematic wide shot mixed with character close-ups, dynamic composition.
Texture: clean line art, smooth color fills, detailed background painting, soft gradients in sky.
```

---

## Story Templates

| Type | Description | Default Style | Example Vocab |
|------|-------------|---------------|---------------|
| fantasy_adventure | Castles, forests, friendly magic | photoreal | castle, forest, dragon, wizard, tower, crystal cave |
| space_explorer | Planets, moonbases, robots | photoreal | moonbase, robot, comet, star map, nebula, space whale |
| animal_quest | Talking animals, nature adventures | photoreal | burrow, river, meadow, hollow tree, berry patch |
| superhero_mission | Kid-friendly heroics, teamwork | photoreal | headquarters, shield, cape, gadget, force field |
| royal_tale | Palaces, gardens, elegant adventures | photoreal | palace, garden, throne, crown, rose maze, fountain |

Safety rules (all templates): No violence. No romance. No free-prompting from users. Only pre-approved entities. Happy or hopeful endings only.

---

## Art Styles

| Style | Prompt Suffix |
|-------|--------------|
| cinematic_photorealism (default) | cinematic photorealistic style, soft depth of field, golden hour lighting, warm tones |
| storybook_watercolor | watercolor illustration, children's storybook art, soft lighting, warm tones |
| anime | anime style, vibrant colors, expressive characters, Studio Ghibli inspired |
| realistic | photorealistic, cinematic lighting, detailed environment, realistic characters |
| comic_book | comic book art, bold outlines, dynamic composition, vivid colors |

Start with photorealism. Get the pipeline working first. Style exploration is second layer.

---

## Supabase (Optional)

Only add if someone on the team already knows Supabase. Without it, everything works in-memory for the demo.

### What it adds:
- Stories persist in Postgres across sessions
- Images hosted in Supabase Storage with public URLs
- Parent auth via Supabase Auth
- Storefront shows all previously saved stories

### Setup (15 min):
1. Create free project at supabase.com
2. Create tables: parents, children, stories
3. Create public images bucket in Storage
4. Copy project URL + anon key to .env
5. pip install supabase + npm install @supabase/supabase-js
6. Disable Row Level Security on all tables

### Gotchas:
- Storage bucket defaults to private (toggle to public)
- RLS blocks all reads/writes (disable for hackathon)
- CORS errors between FastAPI and Supabase (add to CORS config)
- Auth tokens expire after 1 hour (set up refresh or skip auth)

---

## Key Files

| File | What |
|------|------|
| StoryWorld Architecture Reference v2.html | Full architecture reference with SVG diagrams (9 tabs) |
| storyworld-storefront-mockup.html | Storefront UI mockup |
| storyworld_nano_test.py | Image pipeline test script (3-block system) |
| Siena photos | _System/Pipeline/INBOX/Siena/ (3 photos, portrait-img.png is best) |
| Slide deck | StoryWorld Build Reference.html (10 slides) |

---

## What to Build Tomorrow (Priority Order)

1. **Image pipeline test** -- enable billing, run test script with Siena's photo, confirm consistency holds across 3 images
2. **FastAPI backend** -- /generate endpoint that assembles Claude prompt from templates, calls Claude, parses JSON, dispatches image calls
3. **Claude prompt templates** -- age band configs, act structures, story type vocab as hardcoded JSON
4. **Pre-bake one story** -- run the full pipeline once, save the JSON and all images as your fallback
5. **Frontend reader** -- renders story JSON on iPad, scene by scene, images fill in, side panel on entity tap
6. **Polish** -- progressive image loading, error handling, demo flow

---

## API Keys Needed

| Service | Key | Status |
|---------|-----|--------|
| Claude (Anthropic) | ANTHROPIC_API_KEY | Need to confirm |
| Image Gen (Google) | GOOGLE_AI_API_KEY | Have key (AIzaSyA...), needs billing enabled |

---

## Team Context

- Arash: architect, backend, pipeline
- Sylvan: frontend / UI (assigned to reader + panel)
- Hackathon: SoCal Hackathon at UCLA, April 19, 2026
- Theme: Social Impact
- Demo device: iPad
- Demo child: Siena, age 5
