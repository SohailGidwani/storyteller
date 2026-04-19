# Storyworld — Ground Truth
> Last updated: April 19, 2026. This file is canonical. When in doubt, check here first.

---

## What we're building

A personalized iPad storybook app. Parent uploads a child's photo, types their name, picks an age group. Claude generates a complete story with the child as the hero — illustrated in a consistent art style, with tappable words that open a knowledge side panel. Everything is pre-generated upfront so the child's reading experience has zero latency.

**The demo story:** Siena, age 4–5, fantasy setting. This is what we show judges.

---

## Team & ownership

| Person | Role | Owns |
|--------|------|------|
| Sylvan | Frontend | All Next.js UI — storefront, onboarding, reader, side panel, end screen |
| Andrea | Backend | FastAPI server, Claude story generation, NanoBanana image pipeline, Supabase |
| Sohail | Integration + Backend | Frontend ↔ backend wiring, API contracts, backend support, deployment |
| Arash | Story engine + Demo | Claude system prompt, story JSON validation, demo script, presentation |

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
│   │   ├── claude_service.py      # Anthropic API, prompt logic
│   │   ├── image_service.py       # NanoBanana + fallback
│   │   └── supabase_service.py    # DB + storage
│   ├── models/
│   │   └── story.py               # Pydantic models
│   ├── prompts/
│   │   └── story_system.txt       # Claude system prompt (Arash owns this)
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

```json
{
  "story_id": "uuid-string",
  "status": "complete | generating | failed",
  "child": {
    "name": "Siena",
    "age_group": "4-5",
    "photo_url": "https://..."
  },
  "meta": {
    "title": "Siena and the Hidden Door",
    "setting": "fantasy",
    "focus": "adventure",
    "art_style": "watercolor"
  },
  "scenes": [
    {
      "scene_id": 1,
      "chapter_title": "The Morning",
      "prose": "Siena pushed open the tall wooden door of the old castle. Inside, a long hall stretched toward a single lantern, swinging in the dark.",
      "illustration_url": "https://... | null",
      "tappable_words": [
        {
          "word": "castle",
          "char_offset": 42,
          "lore": {
            "name": "Castle",
            "blurb": "Castles are homes with bones of stone. Thick walls keep winter out.",
            "image_url": "https://... | null",
            "curiosity_question": "Who might have lived here?"
          }
        }
      ]
    }
  ]
}
```

**Rules:**
- `illustration_url` and `lore.image_url` may be `null` — frontend must handle gracefully with a placeholder
- `char_offset` is the character index of the word's first letter in `prose` — frontend uses this to inject tappable spans
- `status` field drives the frontend loading state

---

## API endpoints

| Method | Path | Body | Returns | Owner |
|--------|------|------|---------|-------|
| `POST` | `/upload-photo` | `multipart/form-data: file` | `{ photo_url: string }` | Andrea |
| `POST` | `/generate` | `GenerateRequest` | `{ story_id, status, story? }` | Andrea |
| `GET` | `/story/{story_id}` | — | `StoryJSON` | Andrea |
| `GET` | `/health` | — | `{ ok: true }` | Andrea |

**GenerateRequest body:**
```json
{
  "child_name": "Siena",
  "age_group": "4-5",
  "photo_url": "https://...",
  "setting": "fantasy",
  "focus": "adventure",
  "art_style": "watercolor"
}
```

**CORS:** Backend must allow `http://localhost:3000` for local dev.

---

## Cognitive load rules by age group

These are hard constraints in Claude's system prompt. Do not adjust without Arash.

| Parameter | Age 4–5 | Age 6–8 | Age 9–12 |
|-----------|---------|---------|---------|
| Scenes | 3 | 5 | 7 |
| Sentences per block | 2 | 4 | 6 |
| Words per sentence | 8 | 12 | 16 |
| Entities per scene | 2 | 4 | 5 |
| Lore length | 1 sentence | 3 sentences | 5 sentences |
| Flesch–Kincaid target | Grade 1 | Grade 3 | Grade 5 |

---

## Image pipeline

```
Every image call = REFERENCE PHOTO + STYLE BLOCK + SCENE BLOCK

1. Hero portrait  — photo in → styled character out. Generated first. Anchors all scene images.
2. Scene images   — child in story moments. photo + style string + scene description.
3. Entity images  — side panel objects/locations. style + scene only, no child photo needed.
```

- **Primary:** NanoBanana (image-to-image, free with Google account)
- **Fallback:** DALL-E via OpenAI API
- Style block is identical string on every single call (locked per story)
- AI has no memory between calls — every prompt carries full context

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
- **Tappable words:** Dotted underline only — no highlight color, no icon. Clean.
- **Side panel:** Slides in from right, doesn't replace the scene. Dismiss with × or tap outside.
- **Navigation:** Swipe right-to-left to advance scenes. Back arrow for returning.
- **Color:** Warm cream backgrounds. Earthy, storybook palette. Avoid primary-color toy aesthetic.
- **No loading spinners on the reader** — text renders first, images fade in when ready.

---

## Day-of checkpoints

The team calls these checkpoints together. If any fail, activate fallback — do not keep debugging.

| Time | Checkpoint | Fallback |
|------|-----------|---------|
| 11:00am | Valid story JSON generating from Claude? | Load `demo_story.json` |
| 12:00pm | Frontend rendering from backend? | Frontend loads local JSON |
| 1:30pm | Images flowing from NanoBanana? | Placeholder images |
| 2:30pm | Full demo flow works on iPad 3×? | Cut any broken feature |
| **2:30pm** | **FEATURE FREEZE** | No new features after this |
| 4:00pm | Submitted to Devpost | — |

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