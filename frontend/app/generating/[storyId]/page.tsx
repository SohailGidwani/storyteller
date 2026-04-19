'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { getStory } from '@/lib/api'

const MESSAGES = [
  'Writing your adventure…',
  'Painting the illustrations…',
  'Adding the magic…',
  'Almost ready…',
]

export default function GeneratingPage() {
  const router = useRouter()
  const params = useParams()
  const storyId = params.storyId as string

  const [messageIndex, setMessageIndex] = useState(0)
  const [dots, setDots] = useState('')

  // Rotate message every 4s
  useEffect(() => {
    const t = setInterval(() => {
      setMessageIndex((i) => (i + 1) % MESSAGES.length)
    }, 4000)
    return () => clearInterval(t)
  }, [])

  // Animate dots
  useEffect(() => {
    const t = setInterval(() => {
      setDots((d) => (d.length >= 3 ? '' : d + '.'))
    }, 500)
    return () => clearInterval(t)
  }, [])

  // Poll until complete, then redirect to reader
  useEffect(() => {
    let cancelled = false
    let attempts = 0
    const MAX_ATTEMPTS = 90 // 3 minutes at 2s intervals

    const poll = setInterval(async () => {
      attempts++
      if (attempts > MAX_ATTEMPTS) {
        clearInterval(poll)
        if (!cancelled) router.push(`/reader/${storyId}`)
        return
      }
      try {
        const story = await getStory(storyId)
        if (story.status === 'complete' || story.status === 'failed') {
          clearInterval(poll)
          if (!cancelled) router.push(`/reader/${storyId}`)
        }
      } catch {
        // keep polling — transient error
      }
    }, 2000)

    return () => {
      cancelled = true
      clearInterval(poll)
    }
  }, [storyId, router])

  return (
    <div className="h-screen bg-cream flex flex-col items-center justify-center gap-8 px-8">
      {/* Animated book */}
      <div className="relative">
        <svg
          viewBox="0 0 80 60"
          className="w-24 h-24 text-amber animate-pulse"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M40 10 C30 8, 10 10, 8 15 L8 52 C10 47, 30 45, 40 48 C50 45, 70 47, 72 52 L72 15 C70 10, 50 8, 40 10Z"
          />
          <line x1="40" y1="10" x2="40" y2="48" strokeLinecap="round" />
        </svg>

        {/* Pages turning shimmer */}
        <div className="absolute inset-0 rounded-full bg-amber/10 animate-ping" />
      </div>

      {/* Message */}
      <div className="text-center space-y-3">
        <h1 className="font-lora text-sienna text-3xl">
          {MESSAGES[messageIndex]}{dots}
        </h1>
        <p className="font-nunito text-ink/40 text-base max-w-xs">
          Your personalised storybook is being created. This takes about a minute.
        </p>
      </div>

      {/* Progress bar */}
      <div className="w-64 h-1.5 bg-parchment rounded-full overflow-hidden">
        <div className="h-full bg-amber rounded-full animate-[progress_60s_linear_forwards]" />
      </div>
    </div>
  )
}
