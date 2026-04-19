import Link from 'next/link'
import StoryCard from './StoryCard'
import type { StoryCard as StoryCardType } from '@/lib/types'

interface LibraryProps {
  stories: StoryCardType[]
  onDeleted: (storyId: string) => void
}

export default function Library({ stories, onDeleted }: LibraryProps) {
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
        <StoryCard key={story.story_id} story={story} onDeleted={onDeleted} />
      ))}
    </div>
  )
}
