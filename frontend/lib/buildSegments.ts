import type { ClickableEntity } from './types'

export type Segment = { text: string; entity?: ClickableEntity }

type Match = { start: number; end: number; entity: ClickableEntity }

export function buildSegments(content: string, entities: ClickableEntity[]): Segment[] {
  const sorted = [...entities].sort((a, b) => b.word_in_text.length - a.word_in_text.length)

  const matches: Match[] = []

  for (const entity of sorted) {
    const escaped = entity.word_in_text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const regex = new RegExp(`\\b${escaped}\\b`, 'gi')
    let m: RegExpExecArray | null
    while ((m = regex.exec(content)) !== null) {
      const start = m.index
      const end = start + m[0].length
      const overlaps = matches.some(e => start < e.end && end > e.start)
      if (!overlaps) {
        matches.push({ start, end, entity })
      }
    }
  }

  matches.sort((a, b) => a.start - b.start)

  const segments: Segment[] = []
  let cursor = 0
  for (const { start, end, entity } of matches) {
    if (cursor < start) segments.push({ text: content.slice(cursor, start) })
    segments.push({ text: content.slice(start, end), entity })
    cursor = end
  }
  if (cursor < content.length) segments.push({ text: content.slice(cursor) })

  return segments
}
