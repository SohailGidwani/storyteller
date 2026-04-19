import type { GenerateRequest, StoryCard, StoryJSON, StoryStatus } from './types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

const BASE_HEADERS: Record<string, string> = {
  'ngrok-skip-browser-warning': 'true',
}

export async function getStory(storyId: string): Promise<StoryJSON> {
  const res = await fetch(`${BASE_URL}/story/${storyId}`, {
    headers: BASE_HEADERS,
    signal: AbortSignal.timeout(10_000),
  })
  if (!res.ok) throw new Error(`getStory failed: ${res.status}`)
  const data = await res.json()
  if (!Array.isArray(data?.scenes)) throw new Error('Malformed story response')
  return data as StoryJSON
}

export async function generateStory(
  req: GenerateRequest
): Promise<{ story_id: string; status: StoryStatus; story?: StoryJSON }> {
  const res = await fetch(`${BASE_URL}/generate`, {
    method: 'POST',
    headers: { ...BASE_HEADERS, 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
    signal: AbortSignal.timeout(30_000),
  })
  if (!res.ok) throw new Error(`generateStory failed: ${res.status}`)
  return res.json()
}

export async function uploadPhoto(file: File): Promise<{ photo_url: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE_URL}/upload-photo`, {
    method: 'POST',
    headers: BASE_HEADERS,
    body: form,
    signal: AbortSignal.timeout(30_000),
  })
  if (!res.ok) throw new Error(`uploadPhoto failed: ${res.status}`)
  return res.json()
}

export async function healthCheck(): Promise<{ ok: true }> {
  const res = await fetch(`${BASE_URL}/health`, { headers: BASE_HEADERS })
  if (!res.ok) throw new Error('Backend unreachable')
  return res.json()
}

export async function listStories(): Promise<StoryCard[]> {
  const res = await fetch(`${BASE_URL}/stories`, {
    headers: BASE_HEADERS,
    signal: AbortSignal.timeout(10_000),
  })
  if (!res.ok) return []
  return res.json()
}

export async function deleteStory(storyId: string): Promise<void> {
  await fetch(`${BASE_URL}/story/${storyId}`, {
    method: 'DELETE',
    headers: BASE_HEADERS,
    signal: AbortSignal.timeout(10_000),
  })
}
