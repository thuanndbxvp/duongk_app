-- ============================================================
-- Migration: 0039_drop_unused_columns.sql
-- Purpose: Phase 6 — DB Cleanup, remove 12 unused columns
-- ============================================================

-- voice_profiles: drop unused audio params
ALTER TABLE public.voice_profiles DROP COLUMN IF EXISTS pitch;
ALTER TABLE public.voice_profiles DROP COLUMN IF EXISTS tone;
ALTER TABLE public.voice_profiles DROP COLUMN IF EXISTS speed;

-- scripts: drop debug-only columns
ALTER TABLE public.scripts DROP COLUMN IF EXISTS last_token_count;

-- projects: drop unused soft-delete (use status instead)
ALTER TABLE public.projects DROP COLUMN IF EXISTS deleted_at;
-- archived_at: KEEP (UI planned)

-- jobs: drop unused columns
ALTER TABLE public.jobs DROP COLUMN IF EXISTS debug_log;
ALTER TABLE public.jobs DROP COLUMN IF EXISTS worker_node;

-- assets: drop unused columns
ALTER TABLE public.assets DROP COLUMN IF EXISTS original_filename;
ALTER TABLE public.assets DROP COLUMN IF EXISTS download_count;

-- channel_assistants: drop unused
ALTER TABLE public.channel_assistants DROP COLUMN IF EXISTS scrape_config;
ALTER TABLE public.channel_assistants DROP COLUMN IF EXISTS raw_metadata;
