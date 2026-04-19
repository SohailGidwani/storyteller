export type AgeBand = '4-5' | '6-8' | '9+'
export type ActStructure = '3_act' | '5_act' | '7_act'
export type StoryType =
  | 'fantasy_adventure'
  | 'space_explorer'
  | 'animal_quest'
  | 'superhero_mission'
  | 'royal_tale'
export type EntityType = 'character' | 'location' | 'object' | 'creature'
export type StoryStatus = 'complete' | 'generating' | 'failed'

export interface ClickableEntity {
  entity_id: string
  word_in_text: string
  name: string
  type: EntityType
  lore: string
  image_prompt: string
  image_url: string | null
  questions: string[]
}

export type TextBlock =
  | { type: 'text'; content: string }
  | { type: 'image_slot'; prompt: string; alt: string; image_url: string | null }

export interface Scene {
  scene_id: string
  act: number
  act_name: string
  title: string
  text_blocks: TextBlock[]
  clickable_entities: ClickableEntity[]
  navigation: { next_scene_id: string | null }
}

export interface StoryJSON {
  story_id: string
  status: StoryStatus
  photo_url: string | null
  title: string
  child_name: string
  age_band: AgeBand
  act_structure: ActStructure
  story_type: StoryType
  scenes: Scene[]
}

export interface GenerateRequest {
  child_name: string
  age: number
  photo_url: string
  story_type: StoryType
  adhd?: boolean
}
