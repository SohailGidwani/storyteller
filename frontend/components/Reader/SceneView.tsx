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
    // Tap right 20% to advance, left 20% to go back
    const rect = e.currentTarget.getBoundingClientRect()
    if (e.clientX > rect.left + rect.width * 0.8) onNext()
    else if (e.clientX < rect.left + rect.width * 0.2) onPrev()
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

      {/* Bottom spacer */}
      <div className="h-16" />
    </div>
  )
}
