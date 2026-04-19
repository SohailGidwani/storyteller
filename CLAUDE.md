# Storyworld - Ground Truth

> Last updated: April 19, 2026. This file is canonical. When in doubt, check here first.

---

## What we're building

A personalized iPad storybook app. Parent uploads a child's photo, types their name, picks an age group. Claude generates a complete story with the child as the hero — illustrated in a consistent art style, with tappable words that open a knowledge side panel. Everything is pre-generated upfront so the child's reading experience has zero latency.

**The demo story:** Siena, age 4–5, fantasy setting. This is what we show judges.

---

## Team & ownership


| Person | Role                  | Owns                                                                         |
| ------ | --------------------- | ---------------------------------------------------------------------------- |
| Sylvan | Frontend              | All Next.js UI — storefront, onboarding, reader, side panel, end screen      |
| Andrea | Backend               | FastAPI server, Claude story generation, NanoBanana image pipeline, Supabase |
| Sohail | Integration + Backend | Frontend ↔ backend wiring, API contracts, backend support, deployment        |
| Arash  | Story engine + Demo   | Claude system prompt, story JSON validation, demo script, presentation       |


---

## Tech stack

```
Frontend:   Next.js (App Router), TypeScript, Tailwind CSS
Backend:    Python, FastAPI, Supabase (Postgres + Storage)
Image gen:  NanoBanana (image-to-image, primary) → DALL-E (fallback)
LLM:        Claude claude-sonnet-4-20250514 via Anthropic API
Device:     iPad (Safari fullscreen / PWA) — this is the demo device
```

---

## Repo structure

```
storyteller/
├── frontend/               # Next.js app (Sylvan)
│   ├── app/
│   │   ├── page.tsx               # Storefront / library
│   │   ├── create/page.tsx        # Parent onboarding (photo, name, age)
│   │   ├── reader/[storyId]/      # Story reader
│   │   └── layout.tsx
│   ├── components/
│   │   ├── Reader/
│   │   │   ├── SceneView.tsx      # Illustration + prose
│   │   │   ├── TappableText.tsx   # Dotted underline words
│   │   │   └── SidePanel.tsx      # Lore panel
│   │   ├── Storefront/
│   │   │   ├── Library.tsx
│   │   │   └── StoryCard.tsx
│   │   └── Onboarding/
│   │       └── CreateForm.tsx
│   └── lib/
│       ├── api.ts                 # All fetch calls to backend
│       └── types.ts               # Shared TypeScript types (source of truth)
│
├── backend/                # FastAPI app (Andrea + Sohail)
│   ├── main.py
│   ├── routers/
│   │   ├── generate.py            # POST /generate
│   │   ├── stories.py             # GET /story/{id}
│   │   └── upload.py              # POST /upload-photo
│   ├── services/
│   │   ├── claude_service.py      # Anthropic API, prompt assembly (adapted from StoryWorld/claude_prompt_builder.py)
│   │   ├── image_service.py       # NanoBanana + fallback
│   │   └── supabase_service.py    # DB + storage
│   ├── models/
│   │   └── story.py               # Pydantic models
│   ├── prompts/
│   │   ├── cognitive_load_config.json   # Age band params (Arash owns — copy from StoryWorld/)
│   │   └── story_type_templates.json    # Story types + style blocks (Arash owns — copy from StoryWorld/)
│   ├── fixtures/
│   │   └── demo_story.json        # Pre-baked fallback — always keep valid
│   └── requirements.txt
│
├── CLAUDE.md               # This file
└── README.md
```

---

## Story JSON schema

This is the contract between frontend and backend. Do not change without updating `frontend/lib/types.ts` and `backend/models/story.py` in the same commit.

The story JSON has two layers: **generated fields** (produced by Claude, static) and **runtime fields** (added by the backend at serve time, may be null).

```json
{
  "story_id": "uuid-string",
  "status": "complete | generating | failed",
  "photo_url": "https://...",

  "title": "Siena and the Silver Gate",
  "child_name": "Siena",
  "age_band": "4-5",
  "act_structure": "3_act",
  "story_type": "fantasy_adventure",

  "scenes": [
    {
      "scene_id": "scene_1",
      "act": 1,
      "act_name": "The World",
      "title": "The Shimmering Path",
      "text_blocks": [
        { "type": "text", "content": "Siena found a shimmering path." },
        { "type": "image_slot", "prompt": "A child discovering a glowing path...", "alt": "Siena on the path", "image_url": "https://... | null" }
      ],
      "clickable_entities": [
        {
          "entity_id": "ent_gate_1",
          "word_in_text": "silver gate",
          "name": "The Silver Gate",
          "type": "object",
          "lore": "A gate that only opens when you sing.",
          "image_prompt": "An ornate silver gate covered in musical note engravings",
          "image_url": "https://... | null",
          "questions": ["What song does it need?"]
        }
      ],
      "navigation": { "next_scene_id": "scene_2" }
    }
  ]
}
```

**Field notes:**

- `story_id` and `status` are backend runtime fields, not generated by Claude
- `photo_url` is the uploaded child photo URL, added by the backend at serve time
- `scene_id` is a string: `"scene_1"`, `"scene_2"`, etc.
- `navigation.next_scene_id` is `null` on the last scene
- `image_slot.image_url` and `entity.image_url` are `null` until the image pipeline runs — frontend must show a placeholder
- `entity.type` is one of: `"character"`, `"location"`, `"object"`, `"creature"`
- `word_in_text` is the exact phrase as it appears in the preceding `text` block — frontend uses this to inject tappable spans
- `status` field drives the frontend loading state

**Available story types:** `fantasy_adventure`, `space_explorer`, `animal_quest`, `superhero_mission`, `royal_tale`

---

## API endpoints


| Method | Path                | Body                        | Returns                        | Owner  |
| ------ | ------------------- | --------------------------- | ------------------------------ | ------ |
| `POST` | `/upload-photo`     | `multipart/form-data: file` | `{ photo_url: string }`        | Andrea |
| `POST` | `/generate`         | `GenerateRequest`           | `{ story_id, status, story? }` | Andrea |
| `GET`  | `/story/{story_id}` | —                           | `StoryJSON`                    | Andrea |
| `GET`  | `/health`           | —                           | `{ ok: true }`                 | Andrea |


**GenerateRequest body:**

```json
{
  "child_name": "Siena",
  "age": 5,
  "photo_url": "https://...",
  "story_type": "fantasy_adventure",
  "adhd": false
}
```

`age` is the child's integer age — the backend maps it to an age band (`4-5`, `6-8`, `9+`). `story_type` must be one of the five story types listed in the schema section. `adhd` is optional (default `false`) — when true, delivery parameters shift down one band for reduced cognitive load while content complexity stays at the child's level.

**CORS:** Backend must allow `http://localhost:3000` for local dev.

---

## Cognitive load rules by age group

These are hard constraints defined in `StoryWorld/cognitive_load_config.json`. Do not adjust without Arash.


| Parameter                 | Age 4–5    | Age 6–8     | Age 9+      |
| ------------------------- | ---------- | ----------- | ----------- |
| Act structure             | 3-act      | 5-act       | 7-act       |
| Scenes                    | 3          | 5           | 7           |
| Sentences per block       | 2          | 4           | 6           |
| Words per sentence        | 8          | 12          | 16          |
| Image slot every N blocks | 1          | 2           | 3           |
| Entities per scene        | 2          | 4           | 5           |
| Lore length               | 1 sentence | 3 sentences | 5 sentences |
| Questions per entity      | 1          | 3           | 4           |
| Flesch–Kincaid target     | Grade 1    | Grade 3     | Grade 5     |


**ADHD modifier:** When `adhd: true`, the content band stays at the child's age but these delivery parameters shift down one band: `sentences_per_block`, `image_break_every_n_blocks`, `entities_per_scene`, `lore_sentences`, `questions_per_entity`. Age 4–5 is unchanged (already lowest).

---

## Image pipeline

```
Every image call = REFERENCE PHOTO + STYLE BLOCK + SCENE/ENTITY PROMPT

1. Hero portrait  — photo in → styled character out. Generated first. Anchors all scene images.
2. Scene images   — from image_slot.prompt in text_blocks. photo + style + scene prompt.
3. Entity images  — from clickable_entities[].image_prompt. style + entity prompt only, no child photo.
```

- **Primary:** NanoBanana (image-to-image, free with Google account)
- **Fallback:** DALL-E via OpenAI API
- Style block is derived from `story_type_templates.json` → `style_blocks[story_type.default_style]`
- Style block is identical on every call for a given story (locked per story)
- Image prompts never describe the child's appearance — the reference photo handles that
- AI has no memory between calls — every prompt carries full context
- Image results are stored to Supabase and `image_url` is patched back onto the JSON

---

## Fallback strategy (critical)

The demo must not break. Every layer has a fallback:

```
Claude fails        → load fixtures/demo_story.json
Images fail/slow    → show placeholder illustrations, story still reads
Backend unreachable → frontend loads from local demo_story.json directly
```

`fixtures/demo_story.json` must always be a valid, complete story for Siena, age 4–5, fantasy. Arash owns keeping this up to date.

---

## UI design direction

- **Audience:** Kids age 3–12 and their parents
- **Feel:** Warm, book-like, not screen-like. Think physical picture book that happens to be digital.
- **Typography:** Large, rounded, highly legible for young readers. Minimum 18px prose text on iPad.
- **Touch targets:** Minimum 44×44pt for all interactive elements. Kids have imprecise fingers.
- **Clickable entities:** Frontend matches `word_in_text` string in the preceding text block and wraps it in a tappable span. Dotted underline only — no highlight color, no icon. Clean.
- **Side panel:** Slides in from right, doesn't replace the scene. Dismiss with × or tap outside.
- **Navigation:** Swipe right-to-left to advance scenes. Back arrow for returning.
- **Color:** Warm cream backgrounds. Earthy, storybook palette. Avoid primary-color toy aesthetic.
- **No loading spinners on the reader** — text renders first, images fade in when ready.

---

## Day-of checkpoints

The team calls these checkpoints together. If any fail, activate fallback — do not keep debugging.


| Time       | Checkpoint                               | Fallback                   |
| ---------- | ---------------------------------------- | -------------------------- |
| 11:00am    | Valid story JSON generating from Claude? | Load `demo_story.json`     |
| 12:00pm    | Frontend rendering from backend?         | Frontend loads local JSON  |
| 1:30pm     | Images flowing from NanoBanana?          | Placeholder images         |
| 2:30pm     | Full demo flow works on iPad 3×?         | Cut any broken feature     |
| **2:30pm** | **FEATURE FREEZE**                       | No new features after this |
| 4:00pm     | Submitted to Devpost                     | —                          |


---

## Environment variables

```bash
# Backend (.env)
ANTHROPIC_API_KEY=
SUPABASE_URL=
SUPABASE_KEY=
NANOBANA_API_KEY=
OPENAI_API_KEY=          # fallback image gen

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Local dev

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

iPad must be on the same WiFi as the dev machine. Use the machine's local IP (e.g. `http://192.168.x.x:3000`) on Safari.

---

## What "done" looks like

**Minimum viable demo (must have):**

- Parent screen: upload photo, type name, pick age group, hit Generate
- Reader: scene text displays, swipe to advance
- Tappable words: dotted underline, tap opens side panel with lore + question
- Images: load in or gracefully show placeholder
- Works on iPad in Safari

**Nice to have (only if core is solid):**

- Storefront / library screen
- Art style picker
- Smooth page turn animation
- End screen with save to library

---

*When in doubt: ship the core flow. One clean demo beats five half-built features.*



## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools


| Tool                        | Use when                                               |
| --------------------------- | ------------------------------------------------------ |
| `detect_changes`            | Reviewing code changes — gives risk-scored analysis    |
| `get_review_context`        | Need source snippets for review — token-efficient      |
| `get_impact_radius`         | Understanding blast radius of a change                 |
| `get_affected_flows`        | Finding which execution paths are impacted             |
| `query_graph`               | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes`     | Finding functions/classes by name or keyword           |
| `get_architecture_overview` | Understanding high-level codebase structure            |
| `refactor_tool`             | Planning renames, finding dead code                    |


### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.

