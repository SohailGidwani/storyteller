-- Storyworld initial schema

CREATE TABLE IF NOT EXISTS stories (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'generating',
    story_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for status polling
CREATE INDEX IF NOT EXISTS idx_stories_status ON stories (status);
