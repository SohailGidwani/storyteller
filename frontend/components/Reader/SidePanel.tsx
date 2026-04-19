'use client'

import { useRef } from 'react'
import type { ClickableEntity } from '@/lib/types'
import BookIcon from './BookIcon'

interface SidePanelProps {
  entity: ClickableEntity | null
  onClose: () => void
}

export default function SidePanel({ entity, onClose }: SidePanelProps) {
  const lastEntity = useRef<ClickableEntity | null>(null)
  if (entity) lastEntity.current = entity
  const displayed = entity ?? lastEntity.current

  const isOpen = entity !== null

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        className={`fixed inset-0 bg-black/20 z-40 transition-opacity duration-300 ${
          isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
      />

      {/* Panel */}
      <div
        aria-hidden={!isOpen}
        className={`fixed top-0 right-0 h-full w-80 bg-panel shadow-2xl z-50 flex flex-col transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-parchment">
          <h2 className="font-lora text-sienna text-2xl leading-tight pr-4">
            {displayed?.name}
          </h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="w-11 h-11 flex items-center justify-center text-ink/50 hover:text-ink rounded-full shrink-0 -mr-2 -mt-1"
          >
            <span className="text-3xl leading-none">×</span>
          </button>
        </div>

        {/* Entity image */}
        <div className="mx-6 mt-5 aspect-square rounded-xl overflow-hidden bg-parchment flex items-center justify-center">
          {displayed?.image_url ? (
            <img
              src={displayed.image_url}
              alt={displayed.name}
              className="w-full h-full object-contain"
              onError={(e) => {
                e.currentTarget.style.display = 'none'
              }}
            />
          ) : (
            <BookIcon />
          )}
        </div>

        {/* Lore + question */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <p className="font-nunito text-[17px] text-ink leading-relaxed">
            {displayed?.lore}
          </p>

          {displayed?.questions?.[0] && (
            <div className="rounded-xl bg-cream border border-parchment p-4">
              <p className="font-nunito text-xs text-amber uppercase tracking-wide mb-1">
                Wonder about this
              </p>
              <p className="font-nunito text-[16px] text-ink leading-snug">
                {displayed.questions[0]}
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
