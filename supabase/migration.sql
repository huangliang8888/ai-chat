-- =============================================================
-- Supabase Migration: AI Chat Database Schema
-- Run this SQL in your Supabase SQL Editor to set up the tables
-- =============================================================

-- 1. Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast session-based queries
CREATE INDEX IF NOT EXISTS idx_chat_messages_session
    ON chat_messages (session_id, created_at);

-- 2. Row Level Security (optional, for future auth integration)
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- Allow anonymous access for now (adjust when you add auth)
CREATE POLICY "Allow anonymous access to chat_messages"
    ON chat_messages
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- 3. Optional: Auto-delete old messages (runs daily)
-- This keeps the database lean for the free tier
-- CREATE OR REPLACE FUNCTION cleanup_old_messages()
-- RETURNS void AS $$
-- BEGIN
--     DELETE FROM chat_messages
--     WHERE created_at < NOW() - INTERVAL '30 days';
-- END;
-- $$ LANGUAGE plpgsql;
