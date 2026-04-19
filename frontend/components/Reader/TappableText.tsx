'use client'

import { buildSegments } from '@/lib/buildSegments'
import type { ClickableEntity, TextBlock } from '@/lib/types'

interface TappableTextProps {
  block: Extract<TextBlock, { type: 'text' }>
  entities: ClickableEntity[]
  onEntityTap: (entity: ClickableEntity) => void
}

export default function TappableText({ block, entities, onEntityTap }: TappableTextProps) {
  const segments = buildSegments(block.content, entities)

  return (
    <p className="font-nunito text-[19px] leading-relaxed text-ink">
      {segments.map((seg, i) =>
        seg.entity ? (
          <button
            key={i}
            onClick={(e) => {
              e.stopPropagation()
              onEntityTap(seg.entity!)
            }}
            className="border-b-2 border-dotted border-amber bg-transparent text-inherit text-[19px] leading-relaxed p-0 inline cursor-pointer"
          >
            {seg.text}
          </button>
        ) : (
          <span key={i}>{seg.text}</span>
        )
      )}
    </p>
  )
}
