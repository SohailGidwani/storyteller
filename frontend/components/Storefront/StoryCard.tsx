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
