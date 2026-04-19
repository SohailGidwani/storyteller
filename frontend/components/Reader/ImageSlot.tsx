'use client'

import { useState } from 'react'

interface ImageSlotProps {
  imageUrl: string | null
  alt: string
}

function BookIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      className="w-16 h-16 text-amber"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25"
      />
    </svg>
  )
}

export default function ImageSlot({ imageUrl, alt }: ImageSlotProps) {
  const [loaded, setLoaded] = useState(false)

  return (
    <div className="relative w-full aspect-[4/3] rounded-2xl overflow-hidden bg-parchment flex items-center justify-center my-4">
      <BookIcon />
      {imageUrl && (
        <img
          src={imageUrl}
          alt={alt}
          onLoad={() => setLoaded(true)}
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-500 ${
            loaded ? 'opacity-100' : 'opacity-0'
          }`}
        />
      )}
    </div>
  )
}
