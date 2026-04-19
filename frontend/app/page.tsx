'use client'

import { useEffect, useState, useCallback } from 'react'
import Library from '@/components/Storefront/Library'
import type { StoryCard } from '@/lib/types'
import { listStories } from '@/lib/api'

export default function Home() {
  const [stories, setStories] = useState<StoryCard[]>([])
  const [loading, setLoading] = useState(true)

  const fetchStories = useCallback(async () => {
    try {
      const data = await listStories()
      setStories(data)
    } catch {
      setStories([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStories()
    // Re-poll every 5s while any story is still generating
    const interval = setInterval(() => {
      setStories((prev) => {
        if (prev.some((s) => s.status === 'generating')) {
          fetchStories()
        }
        return prev
      })
    }, 5000)
    return () => clearInterval(interval)
  }, [fetchStories])

  function handleDeleted(storyId: string) {
    setStories((prev) => prev.filter((s) => s.story_id !== storyId))
  }

  return (
    <main className="min-h-screen bg-cream">
      <div className="px-8 pt-10 pb-2">
        <h1 className="font-lora text-sienna text-4xl">Your Stories</h1>
        <p className="font-nunito text-ink/50 text-base mt-1">
          Tap a story to read, or create a new one.
        </p>
      </div>

      {loading ? (
        <div className="grid grid-cols-3 gap-5 p-8">
          <div className="aspect-[3/4] rounded-2xl border-2 border-dashed border-parchment flex flex-col items-center justify-center gap-3">
            <span className="text-5xl leading-none text-amber">+</span>
            <span className="font-nunito text-sm text-ink/50">New Story</span>
          </div>
          {[1, 2].map((i) => (
            <div key={i} className="aspect-[3/4] rounded-2xl bg-parchment animate-pulse" />
          ))}
        </div>
      ) : (
        <Library stories={stories} onDeleted={handleDeleted} />
      )}
    </main>
  )
}
