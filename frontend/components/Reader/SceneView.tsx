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
      className="h-full overflow-y-auto"
      style={{ touchAction: 'pan-y' }}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      onClick={handleClick}
    >
      {/* Constrained reading column — comfortable on iPad and laptop */}
      <div className="max-w-2xl mx-auto px-6 py-5">
        {/* Scene title */}
        <h2 className="font-lora text-sienna text-xl mb-4 select-none">
          {scene.title}
        </h2>

        {/* Text blocks in array order */}
        <div className="space-y-3">
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

        <div className="h-8" />
      </div>
    </div>
  )
}
