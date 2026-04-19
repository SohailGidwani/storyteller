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
  | { type: 'STORY_UPDATED'; story: StoryJSON }
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
    case 'STORY_UPDATED':
      return {
        ...state,
        story: action.story,
        currentSceneIndex: Math.min(state.currentSceneIndex, action.story.scenes.length - 1),
      }
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
    let cancelled = false
    let polling: ReturnType<typeof setInterval> | null = null

    async function load() {
      try {
        const story = storyId === 'demo' ? await loadDemoStory() : await getStory(storyId)
        if (cancelled) return

        if (story.status === 'failed') {
          const demo = await loadDemoStory()
          if (!cancelled) dispatch({ type: 'STORY_LOADED', story: demo })
        } else if (story.status === 'generating') {
          dispatch({ type: 'STORY_LOADED', story })
          polling = setInterval(async () => {
            if (cancelled) {
              clearInterval(polling!)
              return
            }
            try {
              const updated = await getStory(storyId)
              if (updated.status !== 'generating') {
                clearInterval(polling!)
                polling = null
                if (!cancelled) {
                  const final = updated.status === 'failed' ? await loadDemoStory() : updated
                  dispatch({ type: 'STORY_UPDATED', story: final })
                }
              }
            } catch {
              // keep polling
            }
          }, 2000)
        } else {
          dispatch({ type: 'STORY_LOADED', story })
        }
      } catch {
        if (!cancelled) {
          try {
            const demo = await loadDemoStory()
            if (!cancelled) dispatch({ type: 'STORY_LOADED', story: demo })
          } catch {
            // nothing to show
          }
        }
      }
    }

    load()
    return () => {
      cancelled = true
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
          type="button"
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
