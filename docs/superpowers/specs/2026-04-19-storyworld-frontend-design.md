# Storyworld Frontend — Design Spec
> Date: 2026-04-19 | Status: Approved

---

## What we're building

A full Next.js (App Router) frontend for a personalized iPad storybook app. Kids age 3–12 read a story where they are the hero. Tapping words opens a lore side panel. Everything is warm, book-like, and distraction-free — no social hooks, no feeds, no links out.

Demo device: iPad Safari landscape (1024×768). Feature freeze: 2:30pm.

---

## Architecture

**Approach: Minimal client-side SPA (Option A)**

- Single `reader/[storyId]/page.tsx` owns all reader state via `useReducer`
- No URL changes between scenes — scenes advance in memory
- Story loaded once on mount, then all navigation is instant
- No external state library — React state only

---

## File Structure

```
frontend/
├── app/
│   ├── layout.tsx                  # Root layout, fonts, global cream background
│   ├── page.tsx                    # Storefront / Library
│   ├── create/page.tsx             # Parent onboarding
│   └── reader/[storyId]/page.tsx   # Story reader — owns all state
├── components/
│   ├── Reader/
│   │   ├── SceneView.tsx           # Renders text_blocks array for one scene + swipe
│   │   ├── TappableText.tsx        # Injects tappable spans into a text block
│   │   └── SidePanel.tsx           # Slides in from right on entity tap
│   ├── Storefront/
│   │   ├── Library.tsx
│   │   └── StoryCard.tsx
│   └── Onboarding/
│       └── CreateForm.tsx
├── lib/
│   ├── types.ts                    # All TypeScript interfaces (Sohail's)
│   └── api.ts                      # All fetch calls (Sohail's)
└── public/
    └── demo_story.json             # Seeded from example_story_age4-5.json + runtime fields
```

---

## Visual Design System

### Fonts
- **Lora** (Google Font) — titles, chapter headings, story title on storefront. Warm serif.
- **Nunito** (Google Font) — prose text, UI labels, side panel content. Rounded, readable for kids.

### Color Tokens (tailwind.config.ts)
```
cream:     #FAF7F2   page background
parchment: #EDE0CC   image placeholders, card backgrounds
ink:       #2C2317   all body text (warm dark brown)
amber:     #C17E3C   interactive accents, entity underlines
sienna:    #8B3A1A   headings, chapter titles
panel:     #FDF5EB   side panel background
```

### Key UI Rules
- Minimum 18px prose text, 22px+ for titles
- Minimum 44×44pt touch targets on all interactive elements
- Tappable entity words: `border-b-2 border-dotted border-amber` — no background, no badge, no icon
- No loading spinners anywhere — placeholders and skeletons only
- Warm cream (`#EDE0CC`) placeholder divs with centered open-book SVG icon in amber

---

## Component Behaviors

### SceneView
- Renders `text_blocks` array top-to-bottom in order
- Each block is either `TappableText` or `ImageSlot`
- Touch events: `touchstart`/`touchend` detect left/right swipes (>50px delta) → advance/retreat scenes
- Tapping right 20% of screen also advances (kids tap more than swipe)
- `navigation.next_scene_id === null` → navigate to end screen

### TappableText
Algorithm for injecting tappable spans into a text block:
1. Sort `clickable_entities` by `word_in_text.length` descending (longest match first, prevents partial matches)
2. Walk text string, find each phrase case-insensitively
3. Strip trailing punctuation before matching (`castle,` matches `castle`)
4. Build array of plain text runs and entity matches
5. Render: plain runs as `<span>`, entity matches as `<button>` with dotted amber underline
6. Only inject entities whose `word_in_text` appears in THIS text block (not all entities in scene)

### SidePanel
- `translate-x-full → translate-x-0`, `transition duration-300`
- Translucent backdrop (`bg-black/20`) on the left — tap to dismiss
- × button top-right to dismiss
- Shows: entity name (Lora, large), lore text (Nunito), entity image or placeholder, first question as "Wonder about this:" prompt
- Only one entity open at a time

### ImageSlot
- `image_url === null` → parchment placeholder div with centered book icon
- `image_url` present → `<img>` with `opacity-0`, transitions to `opacity-100` on `onLoad`
- Never breaks layout regardless of image state

### CreateForm
Single scrollable page (not a wizard):
1. Photo upload with inline preview
2. Child name input
3. Age +/− buttons (range 3–12)
4. Story type: 5 radio tiles with icon + label (`fantasy_adventure`, `space_explorer`, `animal_quest`, `superhero_mission`, `royal_tale`)
5. Generate CTA button

On submit:
1. `POST /upload-photo` with the file
2. `POST /generate` with `{ child_name, age, photo_url, story_type, adhd: false }`
3. `router.push('/reader/[story_id]')`

---

## State Management

```typescript
// reader/[storyId]/page.tsx
type ReaderState = {
  story: StoryJSON | null
  currentSceneIndex: number
  activeEntity: ClickableEntity | null
}

type ReaderAction =
  | { type: 'STORY_LOADED'; story: StoryJSON }
  | { type: 'NEXT_SCENE' }
  | { type: 'PREV_SCENE' }
  | { type: 'OPEN_ENTITY'; entity: ClickableEntity }
  | { type: 'CLOSE_ENTITY' }
```

---

## Data Flow

```
reader/[storyId]/page.tsx
  ├── on mount: GET /story/{id} → if fails → fetch /demo_story.json
  ├── while status==="generating": poll GET /story/{id} every 2s
  │
  ├── SceneView  ← current scene + dispatch
  │   ├── TappableText  ← text block content + scene entities + onEntityTap(entity)
  │   └── ImageSlot     ← image_url (null = placeholder, present = fade in)
  │
  └── SidePanel  ← activeEntity (null = hidden) + onClose
```

### api.ts exports (Sohail's file)
```typescript
getStory(storyId: string): Promise<StoryJSON>
generateStory(req: GenerateRequest): Promise<{ story_id: string; status: string }>
uploadPhoto(file: File): Promise<{ photo_url: string }>
healthCheck(): Promise<{ ok: true }>
```
Base URL: `process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'`

---

## Error Handling & Fallbacks

| Failure | Behavior |
|---------|----------|
| Backend unreachable on reader load | Silently load `public/demo_story.json` |
| `status: "failed"` from backend | Load `demo_story.json` as the story |
| `image_url: null` or image 404 | Show parchment placeholder — layout never breaks |
| `status: "generating"` | Pulsing parchment skeleton blocks — no spinner |
| CreateForm field error | Inline red border + one-line message, no toast/modal |

### demo_story.json seed
Based on `StoryWorld/example_story_age4-5.json` with runtime fields added:
```json
{ "story_id": "demo", "status": "complete", "photo_url": null, ...rest of Siena story }
```

---

## Constraints Carried Forward

- All fetch calls go through `lib/api.ts` — no raw fetch calls in components
- All types imported from `lib/types.ts` — no inline type definitions in components
- Schema changes require updating `types.ts` and `backend/models/story.py` in the same commit
- CORS: backend allows `http://localhost:3000`
- iPad local IP: `NEXT_PUBLIC_API_URL=http://192.168.x.x:8000` on demo day
