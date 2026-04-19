'use client'

import Link from 'next/link'
import { useState } from 'react'
import type { StoryCard } from '@/lib/types'
import { deleteStory } from '@/lib/api'

interface StoryCardProps {
  story: StoryCard
  onDeleted: (storyId: string) => void
}

const STORY_TYPE_ICONS: Record<string, string> = {
  fantasy_adventure: '🏰',
  space_explorer: '🚀',
  animal_quest: '🦊',
  superhero_mission: '⚡',
  royal_tale: '👑',
}

export default function StoryCard({ story, onDeleted }: StoryCardProps) {
  const [deleting, setDeleting] = useState(false)

  async function handleDelete(e: React.MouseEvent) {
    e.preventDefault()
    e.stopPropagation()
    if (!confirm(`Delete "${story.title}"?`)) return
    setDeleting(true)
    try {
      await deleteStory(story.story_id)
      onDeleted(story.story_id)
    } catch {
      setDeleting(false)
    }
  }

  const icon = STORY_TYPE_ICONS[story.story_type] ?? '📖'
  const isGenerating = story.status === 'generating'

  return (
    <div className="relative group">
      <Link
        href={`/reader/${story.story_id}`}
        className={`aspect-[3/4] rounded-2xl flex flex-col justify-end p-5 overflow-hidden relative transition-transform ${
          isGenerating
            ? 'bg-parchment opacity-70 pointer-events-none'
            : 'bg-parchment hover:scale-[1.02] active:scale-[0.98]'
        }`}
      >
        {/* Cover art or placeholder */}
        {story.photo_url ? (
          <img
            src={story.photo_url}
            alt={story.child_name}
            className="absolute inset-0 w-full h-full object-cover opacity-30"
          />
        ) : (
          <span className="absolute top-4 right-4 text-4xl">{icon}</span>
        )}

        {isGenerating && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-8 h-8 border-4 border-amber border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        <div className="relative z-10">
          <span className="font-nunito text-xs text-amber uppercase tracking-wide">
            {story.child_name} · Age {story.age_band}
          </span>
          <h3 className="font-lora text-sienna text-xl leading-snug mt-1">
            {story.title}
          </h3>
        </div>
      </Link>

      {/* Delete button — appears on hover, top-right corner */}
      {!isGenerating && (
        <button
          type="button"
          onClick={handleDelete}
          disabled={deleting}
          aria-label="Delete story"
          className="absolute top-3 right-3 w-8 h-8 rounded-full bg-white/80 flex items-center justify-center text-ink/40 hover:text-red-500 hover:bg-white opacity-0 group-hover:opacity-100 transition-all z-20 shadow-sm"
        >
          {deleting ? (
            <span className="text-xs">…</span>
          ) : (
            <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
              <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          )}
        </button>
      )}
    </div>
  )
}
