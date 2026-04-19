'use client'

import { useState, useEffect } from 'react'
import BookIcon from './BookIcon'

interface ImageSlotProps {
  imageUrl: string | null
  alt: string
}

export default function ImageSlot({ imageUrl, alt }: ImageSlotProps) {
  const [loaded, setLoaded] = useState(false)

  useEffect(() => { setLoaded(false) }, [imageUrl])

  return (
    <div className="relative w-full aspect-[4/3] rounded-2xl overflow-hidden bg-parchment flex items-center justify-center my-4">
      <BookIcon className="w-16 h-16 text-amber" />
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
