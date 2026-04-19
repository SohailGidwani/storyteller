'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import type { StoryType } from '@/lib/types'
import { uploadPhoto, generateStory } from '@/lib/api'

const STORY_TYPES: { id: StoryType; label: string; icon: string }[] = [
  { id: 'fantasy_adventure', label: 'Fantasy', icon: '🏰' },
  { id: 'space_explorer', label: 'Space', icon: '🚀' },
  { id: 'animal_quest', label: 'Animals', icon: '🦊' },
  { id: 'superhero_mission', label: 'Superhero', icon: '⚡' },
  { id: 'royal_tale', label: 'Royalty', icon: '👑' },
]

export default function CreateForm() {
  const router = useRouter()
  const fileRef = useRef<HTMLInputElement>(null)
  const [photoFile, setPhotoFile] = useState<File | null>(null)
  const [photoPreview, setPhotoPreview] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [age, setAge] = useState(5)
  const [storyType, setStoryType] = useState<StoryType>('fantasy_adventure')
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<{ photo?: string; name?: string; submit?: string }>({})

  useEffect(() => {
    return () => {
      if (photoPreview) URL.revokeObjectURL(photoPreview)
    }
  }, [photoPreview])

  function handlePhotoChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    if (photoPreview) URL.revokeObjectURL(photoPreview)
    setPhotoFile(file)
    setPhotoPreview(URL.createObjectURL(file))
    setErrors((prev) => ({ ...prev, photo: undefined }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const nextErrors: typeof errors = {}
    if (!photoFile) nextErrors.photo = 'Please add a photo'
    if (!name.trim()) nextErrors.name = 'Please enter a name'
    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors)
      return
    }

    setLoading(true)
    setErrors({})

    try {
      const { photo_url } = await uploadPhoto(photoFile!)
      const { story_id } = await generateStory({
        child_name: name.trim(),
        age,
        photo_url,
        story_type: storyType,
        adhd: false,
      })
      if (photoPreview) URL.revokeObjectURL(photoPreview)
      router.push(`/generating/${story_id}`)
    } catch {
      setErrors({ submit: 'Something went wrong. Please try again.' })
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-lg mx-auto px-8 py-8 space-y-8">
      {/* Photo */}
      <div>
        <label className="font-lora text-sienna text-xl block mb-3">Photo</label>
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          className={`w-full aspect-square rounded-2xl overflow-hidden flex items-center justify-center transition-colors ${
            errors.photo
              ? 'border-2 border-red-400 bg-red-50'
              : 'bg-parchment hover:bg-parchment/70'
          }`}
        >
          {photoPreview ? (
            <img src={photoPreview} alt="Preview" className="w-full h-full object-cover" />
          ) : (
            <span className="font-nunito text-ink/40 text-center text-sm px-6 leading-relaxed">
              Tap to add a photo of your child
            </span>
          )}
        </button>
        {errors.photo && (
          <p className="font-nunito text-red-500 text-sm mt-1">{errors.photo}</p>
        )}
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          capture="user"
          className="hidden"
          onChange={handlePhotoChange}
        />
      </div>

      {/* Name */}
      <div>
        <label className="font-lora text-sienna text-xl block mb-3">Name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => {
            setName(e.target.value)
            setErrors((prev) => ({ ...prev, name: undefined }))
          }}
          placeholder="Child's first name"
          className={`w-full rounded-xl border-2 px-4 py-3 font-nunito text-ink text-lg focus:outline-none bg-white ${
            errors.name ? 'border-red-400' : 'border-parchment focus:border-amber'
          }`}
        />
        {errors.name && (
          <p className="font-nunito text-red-500 text-sm mt-1">{errors.name}</p>
        )}
      </div>

      {/* Age */}
      <div>
        <label className="font-lora text-sienna text-xl block mb-3">Age: {age}</label>
        <div className="flex items-center gap-6">
          <button
            type="button"
            onClick={() => setAge((a) => Math.max(3, a - 1))}
            className="w-11 h-11 rounded-full bg-parchment font-nunito text-2xl flex items-center justify-center active:bg-amber active:text-white transition-colors"
          >
            −
          </button>
          <span className="font-nunito text-ink text-2xl w-8 text-center tabular-nums">{age}</span>
          <button
            type="button"
            onClick={() => setAge((a) => Math.min(12, a + 1))}
            className="w-11 h-11 rounded-full bg-parchment font-nunito text-2xl flex items-center justify-center active:bg-amber active:text-white transition-colors"
          >
            +
          </button>
        </div>
      </div>

      {/* Story type */}
      <div>
        <label className="font-lora text-sienna text-xl block mb-3">Story World</label>
        <div className="grid grid-cols-5 gap-2">
          {STORY_TYPES.map(({ id, label, icon }) => (
            <button
              key={id}
              type="button"
              onClick={() => setStoryType(id)}
              className={`flex flex-col items-center gap-2 py-3 px-1 rounded-xl border-2 transition-colors ${
                storyType === id
                  ? 'border-amber bg-amber/10'
                  : 'border-parchment hover:border-amber/40'
              }`}
            >
              <span className="text-2xl">{icon}</span>
              <span className="font-nunito text-xs text-ink leading-none">{label}</span>
            </button>
          ))}
        </div>
      </div>

      {errors.submit && (
        <p className="font-nunito text-red-500 text-sm">{errors.submit}</p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full py-4 bg-amber text-white font-nunito text-xl rounded-2xl disabled:opacity-50 active:bg-sienna transition-colors"
      >
        {loading ? 'Creating your story…' : 'Create My Story'}
      </button>
    </form>
  )
}
