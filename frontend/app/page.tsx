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
