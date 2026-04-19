'use client'

import type { ClickableEntity } from '@/lib/types'

interface SidePanelProps {
  entity: ClickableEntity | null
  onClose: () => void
}

function BookIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      className="w-12 h-12 text-amber"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25"
      />
    </svg>
  )
}

export default function SidePanel({ entity, onClose }: SidePanelProps) {
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
        className={`fixed top-0 right-0 h-full w-80 bg-panel shadow-2xl z-50 flex flex-col transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-parchment">
          <h2 className="font-lora text-sienna text-2xl leading-tight pr-4">
            {entity?.name}
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
          {entity?.image_url ? (
            <img
              src={entity.image_url}
              alt={entity.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <BookIcon />
          )}
        </div>

        {/* Lore + question */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <p className="font-nunito text-[17px] text-ink leading-relaxed">
            {entity?.lore}
          </p>

          {entity?.questions?.[0] && (
            <div className="rounded-xl bg-cream border border-parchment p-4">
              <p className="font-nunito text-xs text-amber uppercase tracking-wide mb-1">
                Wonder about this
              </p>
              <p className="font-nunito text-[16px] text-ink leading-snug">
                {entity.questions[0]}
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
