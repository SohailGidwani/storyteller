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
  const touchStartY = useRef<number>(0)
  const didSwipe = useRef<boolean>(false)

  function handleTouchStart(e: React.TouchEvent) {
    touchStartX.current = e.touches[0].clientX
    touchStartY.current = e.touches[0].clientY
    didSwipe.current = false
  }

  function handleTouchEnd(e: React.TouchEvent) {
    const deltaX = touchStartX.current - e.changedTouches[0].clientX
    const deltaY = touchStartY.current - e.changedTouches[0].clientY
    if (Math.abs(deltaX) > 50 && Math.abs(deltaX) > Math.abs(deltaY)) {
      didSwipe.current = true
      if (deltaX > 0) onNext()
      else onPrev()
    }
  }

  function handleClick(e: React.MouseEvent<HTMLDivElement>) {
    if (didSwipe.current) return
    const rect = e.currentTarget.getBoundingClientRect()
    if (e.clientX > rect.left + rect.width * 0.8) onNext()
    else if (e.clientX < rect.left + rect.width * 0.2) onPrev()
  }

  return (
    <div
      className="h-full overflow-y-auto px-8 py-6"
      style={{ touchAction: 'pan-y' }}
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
