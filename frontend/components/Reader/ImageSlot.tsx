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
    <div className="relative w-full rounded-2xl overflow-hidden bg-parchment flex items-center justify-center my-3" style={{ maxHeight: '240px', aspectRatio: '16/9' }}>
      <BookIcon className="w-12 h-12 text-amber" />
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
