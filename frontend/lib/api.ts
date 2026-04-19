import type { GenerateRequest, StoryJSON } from './types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export async function getStory(storyId: string): Promise<StoryJSON> {
  const res = await fetch(`${BASE_URL}/story/${storyId}`)
  if (!res.ok) throw new Error(`getStory failed: ${res.status}`)
  return res.json() as Promise<StoryJSON>
}

export async function generateStory(
  req: GenerateRequest
): Promise<{ story_id: string; status: string }> {
  const res = await fetch(`${BASE_URL}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new Error(`generateStory failed: ${res.status}`)
  return res.json()
}

export async function uploadPhoto(file: File): Promise<{ photo_url: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE_URL}/upload-photo`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new Error(`uploadPhoto failed: ${res.status}`)
  return res.json()
}

export async function healthCheck(): Promise<{ ok: true }> {
  const res = await fetch(`${BASE_URL}/health`)
  if (!res.ok) throw new Error('Backend unreachable')
  return res.json()
}
