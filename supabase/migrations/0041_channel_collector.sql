-- ============================================================
-- Migration: 0041_channel_collector.sql
-- Purpose: Tier 1 P0 — Create channel collector tables
--          Supports YouTube channel tracking and scraping
-- ============================================================

-- ============================================================
-- collector_channels: Track YouTube channels
-- ============================================================
CREATE TABLE IF NOT EXISTS public.collector_channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    name TEXT,
    channel_identifier TEXT,
    thumbnail_url TEXT,
    subscriber_count INTEGER,
    video_count INTEGER,
    recent_videos JSONB DEFAULT '[]'::jsonb,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'error')),
    last_scraped_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(user_id, url)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_collector_channels_user_id ON public.collector_channels(user_id);
CREATE INDEX IF NOT EXISTS idx_collector_channels_url ON public.collector_channels(url);
CREATE INDEX IF NOT EXISTS idx_collector_channels_status ON public.collector_channels(status);

-- Trigger for auto-updating updated_at
CREATE OR REPLACE FUNCTION public.update_collector_channels_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_collector_channels_updated_at ON public.collector_channels;
CREATE TRIGGER trg_collector_channels_updated_at
    BEFORE UPDATE ON public.collector_channels
    FOR EACH ROW EXECUTE FUNCTION public.update_collector_channels_updated_at();

-- RLS Policies
ALTER TABLE public.collector_channels ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own collector channels" ON public.collector_channels;
CREATE POLICY "Users can view their own collector channels"
ON public.collector_channels FOR SELECT
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own collector channels" ON public.collector_channels;
CREATE POLICY "Users can insert their own collector channels"
ON public.collector_channels FOR INSERT
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own collector channels" ON public.collector_channels;
CREATE POLICY "Users can update their own collector channels"
ON public.collector_channels FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own collector channels" ON public.collector_channels;
CREATE POLICY "Users can delete their own collector channels"
ON public.collector_channels FOR DELETE
USING (auth.uid() = user_id);

-- ============================================================
-- collector_scrape_jobs: Track scraping jobs
-- ============================================================
CREATE TABLE IF NOT EXISTS public.collector_scrape_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID NOT NULL REFERENCES public.collector_channels(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    videos_found INTEGER DEFAULT 0,
    error_message TEXT,
    worker_task_id TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_collector_scrape_jobs_channel_id ON public.collector_scrape_jobs(channel_id);
CREATE INDEX IF NOT EXISTS idx_collector_scrape_jobs_user_id ON public.collector_scrape_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_collector_scrape_jobs_status ON public.collector_scrape_jobs(status);
CREATE INDEX IF NOT EXISTS idx_collector_scrape_jobs_created_at ON public.collector_scrape_jobs(created_at DESC);

-- RLS Policies
ALTER TABLE public.collector_scrape_jobs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own scrape jobs" ON public.collector_scrape_jobs;
CREATE POLICY "Users can view their own scrape jobs"
ON public.collector_scrape_jobs FOR SELECT
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own scrape jobs" ON public.collector_scrape_jobs;
CREATE POLICY "Users can insert their own scrape jobs"
ON public.collector_scrape_jobs FOR INSERT
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own scrape jobs" ON public.collector_scrape_jobs;
CREATE POLICY "Users can update their own scrape jobs"
ON public.collector_scrape_jobs FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- ============================================================
-- Function: trigger_scrape for a channel
-- ============================================================
CREATE OR REPLACE FUNCTION public.trigger_channel_scrape(p_channel_id UUID)
RETURNS UUID AS $$
DECLARE
    v_job_id UUID;
    v_user_id UUID;
BEGIN
    -- Get user_id from channel
    SELECT user_id INTO v_user_id FROM collector_channels WHERE id = p_channel_id;
    
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Channel not found';
    END IF;
    
    -- Create scrape job
    INSERT INTO collector_scrape_jobs (channel_id, user_id, status)
    VALUES (p_channel_id, v_user_id, 'pending')
    RETURNING id INTO v_job_id;
    
    RETURN v_job_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================
-- Function: update_scrape_job_status
-- ============================================================
CREATE OR REPLACE FUNCTION public.update_scrape_job_status(
    p_job_id UUID,
    p_status TEXT,
    p_videos_found INTEGER DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE collector_scrape_jobs SET
        status = p_status,
        videos_found = COALESCE(p_videos_found, videos_found),
        error_message = p_error_message,
        completed_at = CASE WHEN p_status IN ('completed', 'failed', 'cancelled') THEN now() ELSE completed_at END,
        started_at = CASE WHEN p_status = 'running' AND started_at IS NULL THEN now() ELSE started_at END
    WHERE id = p_job_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
