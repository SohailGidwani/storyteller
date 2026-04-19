# Storyworld Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold and build the complete Storyworld Next.js frontend — storefront, reader, side panel, and onboarding — targeting iPad Safari landscape.

**Architecture:** Client-side SPA using Next.js App Router. Reader page owns all state via `useReducer`. No scene URL changes — navigation happens in memory. Demo story seeded in `public/demo_story.json` as the unconditional fallback.

**Tech Stack:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Lora + Nunito (Google Fonts), no external state library.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `frontend/` | Create | `create-next-app` scaffold |
| `frontend/tailwind.config.ts` | Replace | Custom color tokens + font families |
| `frontend/app/globals.css` | Replace | Tailwind directives, base body style |
| `frontend/app/layout.tsx` | Replace | Lora + Nunito fonts, cream background |
| `frontend/public/demo_story.json` | Create | Siena demo story with runtime fields |
| `frontend/lib/types.ts` | Create | All TypeScript interfaces |
| `frontend/lib/api.ts` | Create | Typed fetch functions |
| `frontend/lib/buildSegments.ts` | Create | Pure function: injects tappable spans |
| `frontend/lib/__tests__/buildSegments.test.ts` | Create | Unit tests for buildSegments |
| `frontend/components/Reader/TappableText.tsx` | Create | Text block renderer with tappable spans |
| `frontend/components/Reader/ImageSlot.tsx` | Create | Image with placeholder + fade-in |
| `frontend/components/Reader/SidePanel.tsx` | Create | Slide-in entity detail panel |
| `frontend/components/Reader/SceneView.tsx` | Create | Full scene: text_blocks + swipe |
| `frontend/app/reader/[storyId]/page.tsx` | Create | Reader page, state owner |
| `frontend/components/Storefront/StoryCard.tsx` | Create | Book cover tile |
| `frontend/components/Storefront/Library.tsx` | Create | Grid of StoryCards + Create tile |
| `frontend/app/page.tsx` | Replace | Storefront page |
| `frontend/components/Onboarding/CreateForm.tsx` | Create | Photo + name + age + story type form |
| `frontend/app/create/page.tsx` | Create | Onboarding page |
| `frontend/.env.local` | Create | `NEXT_PUBLIC_API_URL` |

---

### Task 1: Scaffold Next.js project

**Files:**
- Create: `frontend/` (via create-next-app)
- Create: `frontend/.env.local`

- [ ] **Step 1: Run create-next-app**

```bash
cd /Users/sohail/Documents/storyteller
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --no-src-dir --import-alias "@/*" --yes
```

Expected: `frontend/` directory created with `app/`, `components/`, `public/`, `package.json`, `tailwind.config.ts`, `tsconfig.json`.

- [ ] **Step 2: Create .env.local**

Create `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

- [ ] **Step 3: Replace tailwind.config.ts**

Replace `frontend/tailwind.config.ts` entirely:
```ts
import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        cream: '#FAF7F2',
        parchment: '#EDE0CC',
        ink: '#2C2317',
        amber: '#C17E3C',
        sienna: '#8B3A1A',
        panel: '#FDF5EB',
      },
      fontFamily: {
        lora: ['var(--font-lora)', 'Georgia', 'serif'],
        nunito: ['var(--font-nunito)', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

export default config
```

- [ ] **Step 4: Replace app/globals.css**

Replace `frontend/app/globals.css` entirely:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

* {
  -webkit-tap-highlight-color: transparent;
}

html, body {
  overscroll-behavior: none;
}
```

- [ ] **Step 5: Replace app/layout.tsx**

Replace `frontend/app/layout.tsx` entirely:
```tsx
import type { Metadata } from 'next'
import { Lora, Nunito } from 'next/font/google'
import './globals.css'

const lora = Lora({
  subsets: ['latin'],
  variable: '--font-lora',
  display: 'swap',
})

const nunito = Nunito({
  subsets: ['latin'],
  variable: '--font-nunito',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Storyworld',
  description: 'Your personalized storybook',
  viewport: 'width=device-width, initial-scale=1, maximum-scale=1',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${lora.variable} ${nunito.variable} bg-cream min-h-screen font-nunito text-ink antialiased`}>
        {children}
      </body>
    </html>
  )
}
```

- [ ] **Step 6: Verify dev server starts**

```bash
cd frontend && npm run dev
```

Expected: server at `http://localhost:3000`, no TypeScript errors. Stop with Ctrl+C.

- [ ] **Step 7: Commit**

```bash
cd /Users/sohail/Documents/storyteller
git add frontend/
git commit -m "feat: scaffold Next.js frontend with Tailwind design tokens"
```

---

### Task 2: Seed demo_story.json

**Files:**
- Create: `frontend/public/demo_story.json`

- [ ] **Step 1: Create demo_story.json**

Create `frontend/public/demo_story.json` with the full content below. This is `StoryWorld/example_story_age4-5.json` with runtime fields added (`story_id`, `status`, `photo_url`) and `image_url: null` injected into every `image_slot` and `clickable_entity`:

```json
{
  "story_id": "demo",
  "status": "complete",
  "photo_url": null,
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
        { "type": "image_slot", "prompt": "A child discovering a glowing path beside a rose garden, soft morning light", "alt": "Siena on the shimmering path", "image_url": null },
        { "type": "text", "content": "A silver gate stood at the end." },
        { "type": "image_slot", "prompt": "An ornate silver gate at the end of a glowing path, roses on both sides, morning mist", "alt": "The silver gate", "image_url": null }
      ],
      "clickable_entities": [
        {
          "entity_id": "ent_gate_1",
          "word_in_text": "silver gate",
          "name": "The Silver Gate",
          "type": "object",
          "lore": "A gate that only opens when you sing.",
          "image_prompt": "An ornate silver gate covered in musical note engravings, ivy on the sides",
          "image_url": null,
          "questions": ["What song does it need?"]
        },
        {
          "entity_id": "ent_path_1",
          "word_in_text": "shimmering path",
          "name": "The Shimmering Path",
          "type": "location",
          "lore": "A path that glows at night.",
          "image_prompt": "A winding path made of glowing stones through a garden, fireflies around it",
          "image_url": null,
          "questions": ["Where does it go?"]
        }
      ],
      "navigation": { "next_scene_id": "scene_2" }
    },
    {
      "scene_id": "scene_2",
      "act": 2,
      "act_name": "The Problem",
      "title": "The Locked Gate",
      "text_blocks": [
        { "type": "text", "content": "The gate would not open." },
        { "type": "image_slot", "prompt": "A child pushing on a large silver gate that won't budge, determined expression", "alt": "Siena tries the gate", "image_url": null },
        { "type": "text", "content": "A small fox sat beside it." },
        { "type": "image_slot", "prompt": "A friendly small red fox sitting beside a silver gate, looking up expectantly", "alt": "The fox by the gate", "image_url": null }
      ],
      "clickable_entities": [
        {
          "entity_id": "ent_fox_1",
          "word_in_text": "fox",
          "name": "The Little Fox",
          "type": "creature",
          "lore": "A friendly fox who knows every path.",
          "image_prompt": "A small red fox with bright eyes sitting in a garden clearing",
          "image_url": null,
          "questions": ["What does the fox know?"]
        },
        {
          "entity_id": "ent_gate_2",
          "word_in_text": "gate",
          "name": "The Silver Gate",
          "type": "object",
          "lore": "A gate that only opens when you sing.",
          "image_prompt": "Close-up of silver gate with musical note engravings glowing faintly",
          "image_url": null,
          "questions": ["How do you open it?"]
        }
      ],
      "navigation": { "next_scene_id": "scene_3" }
    },
    {
      "scene_id": "scene_3",
      "act": 3,
      "act_name": "The Fix",
      "title": "The Song",
      "text_blocks": [
        { "type": "text", "content": "Siena sang her garden song." },
        { "type": "image_slot", "prompt": "A child singing with eyes closed, musical notes floating in the air, flowers blooming", "alt": "Siena sings", "image_url": null },
        { "type": "text", "content": "The gate opened. Flowers came back." },
        { "type": "image_slot", "prompt": "A silver gate swinging open revealing a garden full of colorful flowers, golden light pouring through", "alt": "The gate opens and flowers return", "image_url": null }
      ],
      "clickable_entities": [
        {
          "entity_id": "ent_song_1",
          "word_in_text": "garden song",
          "name": "The Garden Song",
          "type": "object",
          "lore": "A song that makes flowers grow.",
          "image_prompt": "Musical notes floating among blooming flowers, soft golden light",
          "image_url": null,
          "questions": ["What are the words?"]
        },
        {
          "entity_id": "ent_flowers_1",
          "word_in_text": "Flowers",
          "name": "The Garden Flowers",
          "type": "location",
          "lore": "Flowers that dance when they hear music.",
          "image_prompt": "A garden of colorful flowers swaying as if dancing, petals catching light",
          "image_url": null,
          "questions": ["What is their favorite song?"]
        }
      ],
      "navigation": { "next_scene_id": null }
    }
  ]
}
```

- [ ] **Step 2: Verify the JSON is valid**

```bash
cd /Users/sohail/Documents/storyteller/frontend
cat public/demo_story.json | python3 -m json.tool > /dev/null && echo "Valid JSON"
```

Expected: `Valid JSON`

- [ ] **Step 3: Commit**

```bash
cd /Users/sohail/Documents/storyteller
git add frontend/public/demo_story.json
git commit -m "feat: seed demo_story.json with Siena age 4-5 story"
```

---

### Task 3: lib/types.ts

**Files:**
- Create: `frontend/lib/types.ts`

- [ ] **Step 1: Create lib/types.ts**

Create `frontend/lib/types.ts`:
```ts
export type AgeBand = '4-5' | '6-8' | '9+'
export type ActStructure = '3_act' | '5_act' | '7_act'
export type StoryType =
  | 'fantasy_adventure'
  | 'space_explorer'
  | 'animal_quest'
  | 'superhero_mission'
  | 'royal_tale'
export type EntityType = 'character' | 'location' | 'object' | 'creature'
export type StoryStatus = 'complete' | 'generating' | 'failed'

export interface ClickableEntity {
  entity_id: string
  word_in_text: string
  name: string
  type: EntityType
  lore: string
  image_prompt: string
  image_url: string | null
  questions: string[]
}

export type TextBlock =
  | { type: 'text'; content: string }
  | { type: 'image_slot'; prompt: string; alt: string; image_url: string | null }

export interface Scene {
  scene_id: string
  act: number
  act_name: string
  title: string
  text_blocks: TextBlock[]
  clickable_entities: ClickableEntity[]
  navigation: { next_scene_id: string | null }
}

export interface StoryJSON {
  story_id: string
  status: StoryStatus
  photo_url: string | null
  title: string
  child_name: string
  age_band: AgeBand
  act_structure: ActStructure
  story_type: StoryType
  scenes: Scene[]
}

export interface GenerateRequest {
  child_name: string
  age: number
  photo_url: string
  story_type: StoryType
  adhd?: boolean
}
```

- [ ] **Step 2: Check for TypeScript errors**

```bash
cd /Users/sohail/Documents/storyteller/frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
cd /Users/sohail/Documents/storyteller
git add frontend/lib/types.ts
git commit -m "feat: add TypeScript interfaces for story schema"
```

---

### Task 4: lib/api.ts

**Files:**
- Create: `frontend/lib/api.ts`

- [ ] **Step 1: Create lib/api.ts**

Create `frontend/lib/api.ts`:
```ts
import type { GenerateRequest, StoryJSON } from './types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export async function getStory(storyId: string): Promise<StoryJSON> {
  const res = await fetch(`${BASE_URL}/story/${storyId}`)
  if (!res.ok) throw new Error(`getStory failed: ${res.status}`)
  return res.json() as Promise<StoryJSON>
}

export async function generateStory(
  req: GenerateRequest
): Promise<{ story_id: string; status: string }> {
  const res = await fetch(`${BASE_URL}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new Error(`generateStory failed: ${res.status}`)
  return res.json()
}

export async function uploadPhoto(file: File): Promise<{ photo_url: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE_URL}/upload-photo`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new Error(`uploadPhoto failed: ${res.status}`)
  return res.json()
}

export async function healthCheck(): Promise<{ ok: true }> {
  const res = await fetch(`${BASE_URL}/health`)
  if (!res.ok) throw new Error('Backend unreachable')
  return res.json()
}
```

- [ ] **Step 2: Check for TypeScript errors**

```bash
cd /Users/sohail/Documents/storyteller/frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
cd /Users/sohail/Documents/storyteller
git add frontend/lib/api.ts
git commit -m "feat: add typed API client"
```

---

### Task 5: lib/buildSegments.ts + test

**Files:**
- Create: `frontend/lib/buildSegments.ts`
- Create: `frontend/lib/__tests__/buildSegments.test.ts`

This is the core algorithm that injects tappable spans into story text. Test it before building the component.

- [ ] **Step 1: Install Jest**

```bash
cd /Users/sohail/Documents/storyteller/frontend
npm install --save-dev jest @types/jest ts-jest
```

- [ ] **Step 2: Create jest.config.ts**

Create `frontend/jest.config.ts`:
```ts
import type { Config } from 'jest'
import nextJest from 'next/jest.js'

const createJestConfig = nextJest({ dir: './' })

const config: Config = {
  testEnvironment: 'node',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
}

export default createJestConfig(config)
```

- [ ] **Step 3: Write the failing tests**

Create `frontend/lib/__tests__/buildSegments.test.ts`:
```ts
import { buildSegments } from '../buildSegments'
import type { ClickableEntity } from '../types'

function makeEntity(word_in_text: string, entity_id = 'e1'): ClickableEntity {
  return {
    entity_id,
    word_in_text,
    name: word_in_text,
    type: 'object',
    lore: '',
    image_prompt: '',
    image_url: null,
    questions: [],
  }
}

describe('buildSegments', () => {
  it('returns single plain segment when no entities match', () => {
    const result = buildSegments('Hello world.', [makeEntity('fox')])
    expect(result).toEqual([{ text: 'Hello world.' }])
  })

  it('wraps a matching word in an entity segment', () => {
    const entity = makeEntity('fox')
    const result = buildSegments('A small fox sat.', [entity])
    expect(result).toEqual([
      { text: 'A small ' },
      { text: 'fox', entity },
      { text: ' sat.' },
    ])
  })

  it('matches multi-word phrase before single word (longest first)', () => {
    const gate = makeEntity('gate', 'gate')
    const silverGate = makeEntity('silver gate', 'silver_gate')
    const result = buildSegments('A silver gate stood.', [gate, silverGate])
    // "silver gate" should match, not just "gate"
    const entitySegment = result.find(s => s.entity)
    expect(entitySegment?.entity?.entity_id).toBe('silver_gate')
    expect(entitySegment?.text).toBe('silver gate')
  })

  it('is case-insensitive', () => {
    const entity = makeEntity('Flowers')
    const result = buildSegments('The gate opened. Flowers came back.', [entity])
    const entitySegment = result.find(s => s.entity)
    expect(entitySegment?.text).toBe('Flowers')
  })

  it('handles no entities', () => {
    const result = buildSegments('Some text.', [])
    expect(result).toEqual([{ text: 'Some text.' }])
  })

  it('does not double-match overlapping regions', () => {
    const gate = makeEntity('gate', 'gate')
    const silverGate = makeEntity('silver gate', 'silver_gate')
    const result = buildSegments('silver gate here', [gate, silverGate])
    const entitySegments = result.filter(s => s.entity)
    expect(entitySegments).toHaveLength(1)
  })
})
```

- [ ] **Step 4: Run tests — expect FAIL**

```bash
cd /Users/sohail/Documents/storyteller/frontend
npx jest lib/__tests__/buildSegments.test.ts
```

Expected: `Cannot find module '../buildSegments'`

- [ ] **Step 5: Create lib/buildSegments.ts**

Create `frontend/lib/buildSegments.ts`:
```ts
import type { ClickableEntity } from './types'

export type Segment = { text: string; entity?: ClickableEntity }

type Match = { start: number; end: number; entity: ClickableEntity }

export function buildSegments(content: string, entities: ClickableEntity[]): Segment[] {
  const sorted = [...entities].sort((a, b) => b.word_in_text.length - a.word_in_text.length)

  const matches: Match[] = []

  for (const entity of sorted) {
    const escaped = entity.word_in_text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const regex = new RegExp(`\\b${escaped}\\b`, 'gi')
    let m: RegExpExecArray | null
    while ((m = regex.exec(content)) !== null) {
      const start = m.index
      const end = start + m[0].length
      const overlaps = matches.some(e => start < e.end && end > e.start)
      if (!overlaps) {
        matches.push({ start, end, entity })
      }
    }
  }

  matches.sort((a, b) => a.start - b.start)

  const segments: Segment[] = []
  let cursor = 0
  for (const { start, end, entity } of matches) {
    if (cursor < start) segments.push({ text: content.slice(cursor, start) })
    segments.push({ text: content.slice(start, end), entity })
    cursor = end
  }
  if (cursor < content.length) segments.push({ text: content.slice(cursor) })

  return segments
}
```

- [ ] **Step 6: Run tests — expect PASS**

```bash
cd /Users/sohail/Documents/storyteller/frontend
npx jest lib/__tests__/buildSegments.test.ts
```

Expected: `Tests: 6 passed`

- [ ] **Step 7: Commit**

```bash
cd /Users/sohail/Documents/storyteller
git add frontend/lib/buildSegments.ts frontend/lib/__tests__/buildSegments.test.ts frontend/jest.config.ts
git commit -m "feat: add buildSegments utility with passing tests"
```

---

### Task 6: TappableText component

**Files:**
- Create: `frontend/components/Reader/TappableText.tsx`

- [ ] **Step 1: Create components/Reader/TappableText.tsx**

Create `frontend/components/Reader/TappableText.tsx`:
```tsx
'use client'

import { buildSegments } from '@/lib/buildSegments'
import type { ClickableEntity, TextBlock } from '@/lib/types'

interface TappableTextProps {
  block: Extract<TextBlock, { type: 'text' }>
  entities: ClickableEntity[]
  onEntityTap: (entity: ClickableEntity) => void
}

export default function TappableText({ block, entities, onEntityTap }: TappableTextProps) {
  const segments = buildSegments(block.content, entities)

  return (
    <p className="font-nunito text-[19px] leading-relaxed text-ink">
      {segments.map((seg, i) =>
        seg.entity ? (
          <button
            key={i}
            onClick={(e) => {
              e.stopPropagation()
              onEntityTap(seg.entity!)
            }}
            className="border-b-2 border-dotted border-amber bg-transparent text-inherit text-[19px] leading-relaxed p-0 inline cursor-pointer"
          >
            {seg.text}
          </button>
        ) : (
          <span key={i}>{seg.text}</span>
        )
      )}
    </p>
  )
}
```

- [ ] **Step 2: Check TypeScript**

```bash
cd /Users/sohail/Documents/storyteller/frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
cd /Users/sohail/Documents/storyteller
git add frontend/components/Reader/TappableText.tsx
git commit -m "feat: add TappableText component"
```

---

### Task 7: ImageSlot component

**Files:**
- Create: `frontend/components/Reader/ImageSlot.tsx`

- [ ] **Step 1: Create components/Reader/ImageSlot.tsx**

Create `frontend/components/Reader/ImageSlot.tsx`:
```tsx
'use client'

import { useState } from 'react'

interface ImageSlotProps {
  imageUrl: string | null
  alt: string
}

function BookIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      className="w-16 h-16 text-amber"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25"
      />
    </svg>
  )
}

export default function ImageSlot({ imageUrl, alt }: ImageSlotProps) {
  const [loaded, setLoaded] = useState(false)

  return (
    <div className="relative w-full aspect-[4/3] rounded-2xl overflow-hidden bg-parchment flex items-center justify-center my-4">
      <BookIcon />
      {imageUrl && (
        <img
          src={imageUrl}
          alt={alt}
          onLoad={() => setLoaded(true)}
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-500 ${
            loaded ? 'opacity-100' : 'opacity-0'
          }`}
        />
      )}
    </div>
  )
}
```

- [ ] **Step 2: Check TypeScript**

```bash
cd /Users/sohail/Documents/storyteller/frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
cd /Users/sohail/Documents/storyteller
git add frontend/components/Reader/ImageSlot.tsx
git commit -m "feat: add ImageSlot component with fade-in"
```

---

### Task 8: SidePanel component

**Files:**
- Create: `frontend/components/Reader/SidePanel.tsx`

- [ ] **Step 1: Create components/Reader/SidePanel.tsx**

Create `frontend/components/Reader/SidePanel.tsx`:
```tsx
'use client'

import type { ClickableEntity } from '@/lib/types'

interface SidePanelProps {
  entity: ClickableEntity | null
  onClose: () => void
}

function BookIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      className="w-12 h-12 text-amber"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25"
      />
    </svg>
  )
}

export default function SidePanel({ entity, onClose }: SidePanelProps) {
  const isOpen = entity !== null

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        className={`fixed inset-0 bg-black/20 z-40 transition-opacity duration-300 ${
          isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
      />

      {/* Panel */}
      <div
        className={`fixed top-0 right-0 h-full w-80 bg-panel shadow-2xl z-50 flex flex-col transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-parchment">
          <h2 className="font-lora text-sienna text-2xl leading-tight pr-4">
            {entity?.name}
          </h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="w-11 h-11 flex items-center justify-center text-ink/50 hover:text-ink rounded-full shrink-0 -mr-2 -mt-1"
          >
            <span className="text-3xl leading-none">×</span>
          </button>
        </div>

        {/* Entity image */}
        <div className="mx-6 mt-5 aspect-square rounded-xl overflow-hidden bg-parchment flex items-center justify-center">
          {entity?.image_url ? (
            <img
              src={entity.image_url}
              alt={entity.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <BookIcon />
          )}
        </div>

        {/* Lore + question */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <p className="font-nunito text-[17px] text-ink leading-relaxed">
            {entity?.lore}
          </p>

          {entity?.questions?.[0] && (
            <div className="rounded-xl bg-cream border border-parchment p-4">
              <p className="font-nunito text-xs text-amber uppercase tracking-wide mb-1">
                Wonder about this
              </p>
              <p className="font-nunito text-[16px] text-ink leading-snug">
                {entity.questions[0]}
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
```

- [ ] **Step 2: Check TypeScript**

```bash
cd /Users/sohail/Documents/storyteller/frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
cd /Users/sohail/Documents/storyteller
git add frontend/components/Reader/SidePanel.tsx
git commit -m "feat: add SidePanel component"
```

---

### Task 9: SceneView component

**Files:**
- Create: `frontend/components/Reader/SceneView.tsx`

- [ ] **Step 1: Create components/Reader/SceneView.tsx**

Create `frontend/components/Reader/SceneView.tsx`:
```tsx
'use client'

import { useRef } from 'react'
import type { ClickableEntity, Scene } from '@/lib/types'
import TappableText from './TappableText'
import ImageSlot from './ImageSlot'

interface SceneViewProps {
  scene: Scene
  onNext: () => void
  onPrev: () => void
  onEntityTap: (entity: ClickableEntity) => void
}

export default function SceneView({ scene, onNext, onPrev, onEntityTap }: SceneViewProps) {
  const touchStartX = useRef<number>(0)

  function handleTouchStart(e: React.TouchEvent) {
    touchStartX.current = e.touches[0].clientX
  }

  function handleTouchEnd(e: React.TouchEvent) {
    const delta = touchStartX.current - e.changedTouches[0].clientX
    if (delta > 50) onNext()
    else if (delta < -50) onPrev()
  }

  function handleClick(e: React.MouseEvent<HTMLDivElement>) {
    // Tap right 20% of screen to advance
    const rect = e.currentTarget.getBoundingClientRect()
    if (e.clientX > rect.left + rect.width * 0.8) onNext()
  }

  return (
    <div
      className="h-full overflow-y-auto px-8 py-6"
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      onClick={handleClick}
    >
      {/* Scene title */}
      <h2 className="font-lora text-sienna text-2xl mb-6 select-none">
        {scene.title}
      </h2>

      {/* Text blocks in array order */}
      <div className="space-y-4">
        {scene.text_blocks.map((block, i) => {
          if (block.type === 'text') {
            return (
              <TappableText
                key={i}
                block={block}
                entities={scene.clickable_entities}
                onEntityTap={onEntityTap}
              />
            )
          }
          return (
            <ImageSlot
              key={i}
              imageUrl={block.image_url}
              alt={block.alt}
            />
          )
        })}
      </div>

      {/* Bottom spacer for comfortable reading */}
      <div className="h-16" />
    </div>
  )
}
```

- [ ] **Step 2: Check TypeScript**

```bash
cd /Users/sohail/Documents/storyteller/frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
cd /Users/sohail/Documents/storyteller
git add frontend/components/Reader/SceneView.tsx
git commit -m "feat: add SceneView with swipe navigation"
```

---

### Task 10: Reader page

**Files:**
- Create: `frontend/app/reader/[storyId]/page.tsx`

- [ ] **Step 1: Create app/reader/[storyId]/page.tsx**

Create `frontend/app/reader/[storyId]/page.tsx`:
```tsx
'use client'

import { useReducer, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import type { ClickableEntity, StoryJSON } from '@/lib/types'
import { getStory } from '@/lib/api'
import SceneView from '@/components/Reader/SceneView'
import SidePanel from '@/components/Reader/SidePanel'

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

function reducer(state: ReaderState, action: ReaderAction): ReaderState {
  switch (action.type) {
    case 'STORY_LOADED':
      return { ...state, story: action.story, currentSceneIndex: 0, activeEntity: null }
    case 'NEXT_SCENE':
      if (!state.story) return state
      return {
        ...state,
        currentSceneIndex: Math.min(state.currentSceneIndex + 1, state.story.scenes.length - 1),
        activeEntity: null,
      }
    case 'PREV_SCENE':
      return {
        ...state,
        currentSceneIndex: Math.max(state.currentSceneIndex - 1, 0),
        activeEntity: null,
      }
    case 'OPEN_ENTITY':
      return { ...state, activeEntity: action.entity }
    case 'CLOSE_ENTITY':
      return { ...state, activeEntity: null }
    default:
      return state
  }
}

async function loadDemoStory(): Promise<StoryJSON> {
  const res = await fetch('/demo_story.json')
  if (!res.ok) throw new Error('demo_story.json not found')
  return res.json() as Promise<StoryJSON>
}

function ReaderSkeleton() {
  return (
    <div className="h-screen bg-cream flex flex-col">
      <div className="flex items-center justify-between px-8 py-4 border-b border-parchment">
        <div className="w-8 h-8 bg-parchment rounded-lg animate-pulse" />
        <div className="w-48 h-6 bg-parchment rounded animate-pulse" />
        <div className="w-10 h-4 bg-parchment rounded animate-pulse" />
      </div>
      <div className="flex-1 px-8 py-6 space-y-4">
        <div className="h-8 w-56 bg-parchment rounded-lg animate-pulse" />
        <div className="h-5 w-full bg-parchment rounded animate-pulse" />
        <div className="h-5 w-4/5 bg-parchment rounded animate-pulse" />
        <div className="w-full aspect-[4/3] bg-parchment rounded-2xl animate-pulse" />
        <div className="h-5 w-full bg-parchment rounded animate-pulse" />
        <div className="h-5 w-2/3 bg-parchment rounded animate-pulse" />
      </div>
    </div>
  )
}

export default function ReaderPage() {
  const params = useParams()
  const router = useRouter()
  const storyId = params.storyId as string

  const [state, dispatch] = useReducer(reducer, {
    story: null,
    currentSceneIndex: 0,
    activeEntity: null,
  })

  useEffect(() => {
    let polling: ReturnType<typeof setInterval> | null = null

    async function load() {
      try {
        const story = storyId === 'demo' ? await loadDemoStory() : await getStory(storyId)

        if (story.status === 'failed') {
          dispatch({ type: 'STORY_LOADED', story: await loadDemoStory() })
        } else if (story.status === 'generating') {
          dispatch({ type: 'STORY_LOADED', story })
          polling = setInterval(async () => {
            try {
              const updated = await getStory(storyId)
              if (updated.status !== 'generating') {
                clearInterval(polling!)
                polling = null
                const final = updated.status === 'failed' ? await loadDemoStory() : updated
                dispatch({ type: 'STORY_LOADED', story: final })
              }
            } catch {
              // keep polling
            }
          }, 2000)
        } else {
          dispatch({ type: 'STORY_LOADED', story })
        }
      } catch {
        try {
          dispatch({ type: 'STORY_LOADED', story: await loadDemoStory() })
        } catch {
          // truly broken — nothing to show
        }
      }
    }

    load()
    return () => {
      if (polling) clearInterval(polling)
    }
  }, [storyId])

  const { story, currentSceneIndex, activeEntity } = state

  if (!story) return <ReaderSkeleton />

  const currentScene = story.scenes[currentSceneIndex]
  const isLastScene = currentScene.navigation.next_scene_id === null

  function handleNext() {
    if (isLastScene) {
      router.push('/')
    } else {
      dispatch({ type: 'NEXT_SCENE' })
    }
  }

  return (
    <div className="h-screen bg-cream flex flex-col overflow-hidden">
      {/* Title bar */}
      <div className="flex items-center justify-between px-8 py-4 border-b border-parchment shrink-0">
        <button
          onClick={() => router.push('/')}
          className="w-11 h-11 flex items-center justify-center text-ink/50 hover:text-ink text-xl"
          aria-label="Back to library"
        >
          ←
        </button>
        <h1 className="font-lora text-sienna text-lg truncate px-2">{story.title}</h1>
        <span className="font-nunito text-ink/40 text-sm tabular-nums">
          {currentSceneIndex + 1}/{story.scenes.length}
        </span>
      </div>

      {/* Scene */}
      <div className="flex-1 overflow-hidden">
        <SceneView
          scene={currentScene}
          onNext={handleNext}
          onPrev={() => dispatch({ type: 'PREV_SCENE' })}
          onEntityTap={(entity) => dispatch({ type: 'OPEN_ENTITY', entity })}
        />
      </div>

      <SidePanel
        entity={activeEntity}
        onClose={() => dispatch({ type: 'CLOSE_ENTITY' })}
      />
    </div>
  )
}
```

- [ ] **Step 2: Check TypeScript**

```bash
cd /Users/sohail/Documents/storyteller/frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Smoke test reader with demo story**

```bash
cd /Users/sohail/Documents/storyteller/frontend
npm run dev
```

Open `http://localhost:3000/reader/demo`. Expected: Siena's story renders — chapter title "The Shimmering Path", prose text with "silver gate" and "shimmering path" as dotted-underline tappable words, parchment placeholders where images will be. Stop server.

- [ ] **Step 4: Commit**

```bash
cd /Users/sohail/Documents/storyteller
git add frontend/app/reader/
git commit -m "feat: add reader page with useReducer state and demo story fallback"
```

---

### Task 11: Storefront

**Files:**
- Create: `frontend/components/Storefront/StoryCard.tsx`
- Create: `frontend/components/Storefront/Library.tsx`
- Replace: `frontend/app/page.tsx`

- [ ] **Step 1: Create StoryCard.tsx**

Create `frontend/components/Storefront/StoryCard.tsx`:
```tsx
import Link from 'next/link'
import type { StoryJSON } from '@/lib/types'

interface StoryCardProps {
  story: StoryJSON
}

export default function StoryCard({ story }: StoryCardProps) {
  return (
    <Link
      href={`/reader/${story.story_id}`}
      className="aspect-[3/4] rounded-2xl bg-parchment flex flex-col justify-end p-5 overflow-hidden relative hover:scale-[1.02] active:scale-[0.98] transition-transform"
    >
      <span className="font-nunito text-xs text-amber uppercase tracking-wide">
        Age {story.age_band}
      </span>
      <h3 className="font-lora text-sienna text-xl leading-snug mt-1">
        {story.title}
      </h3>
    </Link>
  )
}
```

- [ ] **Step 2: Create Library.tsx**

Create `frontend/components/Storefront/Library.tsx`:
```tsx
import Link from 'next/link'
import StoryCard from './StoryCard'
import type { StoryJSON } from '@/lib/types'

interface LibraryProps {
  stories: StoryJSON[]
}

export default function Library({ stories }: LibraryProps) {
  return (
    <div className="grid grid-cols-3 gap-5 p-8">
      {/* Create new tile */}
      <Link
        href="/create"
        className="aspect-[3/4] rounded-2xl border-2 border-dashed border-parchment flex flex-col items-center justify-center gap-3 hover:bg-parchment/30 active:bg-parchment/50 transition-colors"
      >
        <span className="text-5xl leading-none text-amber">+</span>
        <span className="font-nunito text-sm text-ink/50">New Story</span>
      </Link>

      {stories.map((story) => (
        <StoryCard key={story.story_id} story={story} />
      ))}
    </div>
  )
}
```

- [ ] **Step 3: Replace app/page.tsx**

Replace `frontend/app/page.tsx` entirely:
```tsx
'use client'

import { useEffect, useState } from 'react'
import Library from '@/components/Storefront/Library'
import type { StoryJSON } from '@/lib/types'

export default function Home() {
  const [stories, setStories] = useState<StoryJSON[]>([])

  useEffect(() => {
    fetch('/demo_story.json')
      .then((r) => r.json())
      .then((story: StoryJSON) => setStories([story]))
      .catch(() => setStories([]))
  }, [])

  return (
    <main className="min-h-screen bg-cream">
      <div className="px-8 pt-10 pb-2">
        <h1 className="font-lora text-sienna text-4xl">Your Stories</h1>
        <p className="font-nunito text-ink/50 text-base mt-1">Tap a story to read, or create a new one.</p>
      </div>
      <Library stories={stories} />
    </main>
  )
}
```

- [ ] **Step 4: Check TypeScript**

```bash
cd /Users/sohail/Documents/storyteller/frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 5: Commit**

```bash
cd /Users/sohail/Documents/storyteller
git add frontend/components/Storefront/ frontend/app/page.tsx
git commit -m "feat: add storefront Library and StoryCard"
```

---

### Task 12: CreateForm + onboarding page

**Files:**
- Create: `frontend/components/Onboarding/CreateForm.tsx`
- Create: `frontend/app/create/page.tsx`

- [ ] **Step 1: Create CreateForm.tsx**

Create `frontend/components/Onboarding/CreateForm.tsx`:
```tsx
'use client'

import { useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import type { StoryType } from '@/lib/types'
import { uploadPhoto, generateStory } from '@/lib/api'

const STORY_TYPES: { id: StoryType; label: string; icon: string }[] = [
  { id: 'fantasy_adventure', label: 'Fantasy', icon: '🏰' },
  { id: 'space_explorer', label: 'Space', icon: '🚀' },
  { id: 'animal_quest', label: 'Animals', icon: '🦊' },
  { id: 'superhero_mission', label: 'Superhero', icon: '⚡' },
  { id: 'royal_tale', label: 'Royalty', icon: '👑' },
]

export default function CreateForm() {
  const router = useRouter()
  const fileRef = useRef<HTMLInputElement>(null)
  const [photoFile, setPhotoFile] = useState<File | null>(null)
  const [photoPreview, setPhotoPreview] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [age, setAge] = useState(5)
  const [storyType, setStoryType] = useState<StoryType>('fantasy_adventure')
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<{ photo?: string; name?: string; submit?: string }>({})

  function handlePhotoChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setPhotoFile(file)
    setPhotoPreview(URL.createObjectURL(file))
    setErrors((prev) => ({ ...prev, photo: undefined }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const nextErrors: typeof errors = {}
    if (!photoFile) nextErrors.photo = 'Please add a photo'
    if (!name.trim()) nextErrors.name = 'Please enter a name'
    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors)
      return
    }

    setLoading(true)
    setErrors({})

    try {
      const { photo_url } = await uploadPhoto(photoFile!)
      const { story_id } = await generateStory({
        child_name: name.trim(),
        age,
        photo_url,
        story_type: storyType,
        adhd: false,
      })
      router.push(`/reader/${story_id}`)
    } catch {
      setErrors({ submit: 'Something went wrong. Please try again.' })
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-lg mx-auto px-8 py-8 space-y-8">
      {/* Photo */}
      <div>
        <label className="font-lora text-sienna text-xl block mb-3">Photo</label>
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          className={`w-full aspect-square rounded-2xl overflow-hidden flex items-center justify-center transition-colors ${
            errors.photo
              ? 'border-2 border-red-400 bg-red-50'
              : 'bg-parchment hover:bg-parchment/70'
          }`}
        >
          {photoPreview ? (
            <img src={photoPreview} alt="Preview" className="w-full h-full object-cover" />
          ) : (
            <span className="font-nunito text-ink/40 text-center text-sm px-6 leading-relaxed">
              Tap to add a photo of your child
            </span>
          )}
        </button>
        {errors.photo && (
          <p className="font-nunito text-red-500 text-sm mt-1">{errors.photo}</p>
        )}
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          capture="user"
          className="hidden"
          onChange={handlePhotoChange}
        />
      </div>

      {/* Name */}
      <div>
        <label className="font-lora text-sienna text-xl block mb-3">Name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => {
            setName(e.target.value)
            setErrors((prev) => ({ ...prev, name: undefined }))
          }}
          placeholder="Child's first name"
          className={`w-full rounded-xl border-2 px-4 py-3 font-nunito text-ink text-lg focus:outline-none bg-white ${
            errors.name ? 'border-red-400' : 'border-parchment focus:border-amber'
          }`}
        />
        {errors.name && (
          <p className="font-nunito text-red-500 text-sm mt-1">{errors.name}</p>
        )}
      </div>

      {/* Age */}
      <div>
        <label className="font-lora text-sienna text-xl block mb-3">Age: {age}</label>
        <div className="flex items-center gap-6">
          <button
            type="button"
            onClick={() => setAge((a) => Math.max(3, a - 1))}
            className="w-11 h-11 rounded-full bg-parchment font-nunito text-2xl flex items-center justify-center active:bg-amber active:text-white transition-colors"
          >
            −
          </button>
          <span className="font-nunito text-ink text-2xl w-8 text-center tabular-nums">{age}</span>
          <button
            type="button"
            onClick={() => setAge((a) => Math.min(12, a + 1))}
            className="w-11 h-11 rounded-full bg-parchment font-nunito text-2xl flex items-center justify-center active:bg-amber active:text-white transition-colors"
          >
            +
          </button>
        </div>
      </div>

      {/* Story type */}
      <div>
        <label className="font-lora text-sienna text-xl block mb-3">Story World</label>
        <div className="grid grid-cols-5 gap-2">
          {STORY_TYPES.map(({ id, label, icon }) => (
            <button
              key={id}
              type="button"
              onClick={() => setStoryType(id)}
              className={`flex flex-col items-center gap-2 py-3 px-1 rounded-xl border-2 transition-colors ${
                storyType === id
                  ? 'border-amber bg-amber/10'
                  : 'border-parchment hover:border-amber/40'
              }`}
            >
              <span className="text-2xl">{icon}</span>
              <span className="font-nunito text-xs text-ink leading-none">{label}</span>
            </button>
          ))}
        </div>
      </div>

      {errors.submit && (
        <p className="font-nunito text-red-500 text-sm">{errors.submit}</p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full py-4 bg-amber text-white font-nunito text-xl rounded-2xl disabled:opacity-50 active:bg-sienna transition-colors"
      >
        {loading ? 'Creating your story…' : 'Create My Story'}
      </button>
    </form>
  )
}
```

- [ ] **Step 2: Create app/create/page.tsx**

Create `frontend/app/create/page.tsx`:
```tsx
import CreateForm from '@/components/Onboarding/CreateForm'
import Link from 'next/link'

export default function CreatePage() {
  return (
    <main className="min-h-screen bg-cream">
      <div className="flex items-center gap-4 px-8 pt-10 pb-2">
        <Link
          href="/"
          className="w-11 h-11 flex items-center justify-center text-ink/50 hover:text-ink text-xl"
          aria-label="Back"
        >
          ←
        </Link>
        <h1 className="font-lora text-sienna text-4xl">Make Your Story</h1>
      </div>
      <CreateForm />
    </main>
  )
}
```

- [ ] **Step 3: Check TypeScript**

```bash
cd /Users/sohail/Documents/storyteller/frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
cd /Users/sohail/Documents/storyteller
git add frontend/components/Onboarding/ frontend/app/create/
git commit -m "feat: add CreateForm and onboarding page"
```

---

### Task 13: Full smoke test

- [ ] **Step 1: Run all tests**

```bash
cd /Users/sohail/Documents/storyteller/frontend
npx jest
```

Expected: `Tests: 6 passed, 6 total`

- [ ] **Step 2: TypeScript clean build**

```bash
cd /Users/sohail/Documents/storyteller/frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Start dev server and verify all routes**

```bash
cd /Users/sohail/Documents/storyteller/frontend
npm run dev
```

Check:
- `http://localhost:3000` → storefront with Siena card + "New Story" tile
- `http://localhost:3000/reader/demo` → reader with 3 scenes, tappable words, parchment image placeholders, swipe to advance
- `http://localhost:3000/create` → onboarding form, all fields, story type tiles

Stop server with Ctrl+C.

- [ ] **Step 4: Final commit**

```bash
cd /Users/sohail/Documents/storyteller
git add -A
git commit -m "feat: complete Storyworld frontend — reader, storefront, onboarding"
```

---

## Self-Review

**Spec coverage:**
- ✅ SceneView renders text_blocks (Task 9)
- ✅ TappableText injects word_in_text spans (Tasks 5–6)
- ✅ SidePanel slides in, shows lore + question (Task 8)
- ✅ Scene navigation via swipe + right-tap (Task 9)
- ✅ ImageSlot fade-in + placeholder (Task 7)
- ✅ Reader fallback to demo_story.json (Task 10)
- ✅ Polling while status=generating (Task 10)
- ✅ CreateForm with photo/name/age/story_type (Task 12)
- ✅ Storefront grid (Task 11)
- ✅ Custom color tokens + fonts (Task 1)
- ✅ All fetch calls through api.ts (Tasks 4, 12)
- ✅ All types from types.ts (Task 3)

**Placeholder scan:** None found.

**Type consistency:** `ClickableEntity`, `TextBlock`, `Scene`, `StoryJSON`, `GenerateRequest` defined once in `lib/types.ts`, imported everywhere. `buildSegments` exported from `lib/buildSegments.ts`, imported by `TappableText`. `Segment` type exported alongside `buildSegments` for test access.
