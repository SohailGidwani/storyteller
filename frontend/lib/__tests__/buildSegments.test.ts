import { buildSegments } from '../buildSegments'
import type { ClickableEntity } from '../types'

function makeEntity(word_in_text: string, entity_id = 'e1'): ClickableEntity {
  return {
    entity_id,
    word_in_text,
    name: word_in_text,
    type: 'object',
    lore: '',
    image_prompt: '',
    image_url: null,
    questions: [],
  }
}

describe('buildSegments', () => {
  it('returns single plain segment when no entities match', () => {
    const result = buildSegments('Hello world.', [makeEntity('fox')])
    expect(result).toEqual([{ text: 'Hello world.' }])
  })

  it('wraps a matching word in an entity segment', () => {
    const entity = makeEntity('fox')
    const result = buildSegments('A small fox sat.', [entity])
    expect(result).toEqual([
      { text: 'A small ' },
      { text: 'fox', entity },
      { text: ' sat.' },
    ])
  })

  it('matches multi-word phrase before single word (longest first)', () => {
    const gate = makeEntity('gate', 'gate')
    const silverGate = makeEntity('silver gate', 'silver_gate')
    const result = buildSegments('A silver gate stood.', [gate, silverGate])
    const entitySegment = result.find(s => s.entity)
    expect(entitySegment?.entity?.entity_id).toBe('silver_gate')
    expect(entitySegment?.text).toBe('silver gate')
  })

  it('is case-insensitive', () => {
    const entity = makeEntity('Flowers')
    const result = buildSegments('The gate opened. Flowers came back.', [entity])
    const entitySegment = result.find(s => s.entity)
    expect(entitySegment?.text).toBe('Flowers')
  })

  it('handles no entities', () => {
    const result = buildSegments('Some text.', [])
    expect(result).toEqual([{ text: 'Some text.' }])
  })

  it('does not double-match overlapping regions', () => {
    const gate = makeEntity('gate', 'gate')
    const silverGate = makeEntity('silver gate', 'silver_gate')
    const result = buildSegments('silver gate here', [gate, silverGate])
    const entitySegments = result.filter(s => s.entity)
    expect(entitySegments).toHaveLength(1)
  })
})
