-- ============================================================
-- Migration: 0031_voice_lines_timelines.sql
-- Purpose: Phase 03 — Voice per Scene, SRT & Timeline
-- ============================================================

-- Bảng voice_lines: 1 row per scene per voice version
CREATE TABLE IF NOT EXISTS public.voice_lines (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scene_id uuid NOT NULL REFERENCES public.project_scenes(id) ON DELETE CASCADE,
  voice_profile_id uuid NULL REFERENCES public.voice_profiles(id),
  voice_version int NOT NULL DEFAULT 1,
  text text NOT NULL,
  storage_key text NULL,
  duration_seconds numeric(10,3) NULL,
  provider text NOT NULL DEFAULT 'omnivoice',
  model_version text NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'success', 'failed', 'cancelled')),
  error_code text NULL,
  error_message text NULL,
  started_at timestamptz NULL,
  finished_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (scene_id, voice_version)
);

CREATE INDEX IF NOT EXISTS idx_voice_lines_scene ON public.voice_lines(scene_id);
CREATE INDEX IF NOT EXISTS idx_voice_lines_status ON public.voice_lines(status);

-- Bảng subtitle_tracks: SRT per project version
CREATE TABLE IF NOT EXISTS public.subtitle_tracks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  format text NOT NULL DEFAULT 'srt',
  storage_key text NOT NULL,
  version int NOT NULL DEFAULT 1,
  status text NOT NULL DEFAULT 'draft',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (project_id, version)
);

CREATE INDEX IF NOT EXISTS idx_subtitle_tracks_project ON public.subtitle_tracks(project_id);

-- Bảng timelines: versioned JSON model
CREATE TABLE IF NOT EXISTS public.timelines (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  version int NOT NULL,
  schema_version smallint NOT NULL DEFAULT 1,
  model jsonb NOT NULL DEFAULT '{}'::jsonb,
  status text NOT NULL DEFAULT 'draft',
  created_by uuid NULL REFERENCES auth.users(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (project_id, version)
);

CREATE INDEX IF NOT EXISTS idx_timelines_project ON public.timelines(project_id, version DESC);
-- ============================================================
-- RLS Policies
-- ============================================================
ALTER TABLE public.voice_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subtitle_tracks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.timelines ENABLE ROW LEVEL SECURITY;

-- voice_lines: owner qua scene → project
DROP POLICY IF EXISTS "Users can view own voice lines" ON public.voice_lines;
CREATE POLICY "Users can view own voice lines" ON public.voice_lines FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM public.project_scenes ps
    JOIN public.projects p ON p.id = ps.project_id
    WHERE ps.id = voice_lines.scene_id AND p.user_id = auth.uid()
  ));

DROP POLICY IF EXISTS "Users can insert own voice lines" ON public.voice_lines;
CREATE POLICY "Users can insert own voice lines" ON public.voice_lines FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM public.project_scenes ps
    JOIN public.projects p ON p.id = ps.project_id
    WHERE ps.id = voice_lines.scene_id AND p.user_id = auth.uid()
  ));

DROP POLICY IF EXISTS "Users can update own voice lines" ON public.voice_lines;
CREATE POLICY "Users can update own voice lines" ON public.voice_lines FOR UPDATE
  USING (EXISTS (
    SELECT 1 FROM public.project_scenes ps
    JOIN public.projects p ON p.id = ps.project_id
    WHERE ps.id = voice_lines.scene_id AND p.user_id = auth.uid()
  ));

-- subtitle_tracks: owner qua project
DROP POLICY IF EXISTS "Users can view own subtitles" ON public.subtitle_tracks;
CREATE POLICY "Users can view own subtitles" ON public.subtitle_tracks FOR SELECT
  USING (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = subtitle_tracks.project_id AND p.user_id = auth.uid()));

DROP POLICY IF EXISTS "Users can insert own subtitles" ON public.subtitle_tracks;
CREATE POLICY "Users can insert own subtitles" ON public.subtitle_tracks FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = subtitle_tracks.project_id AND p.user_id = auth.uid()));

-- timelines: owner qua project
DROP POLICY IF EXISTS "Users can view own timelines" ON public.timelines;
CREATE POLICY "Users can view own timelines" ON public.timelines FOR SELECT
  USING (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = timelines.project_id AND p.user_id = auth.uid()));

DROP POLICY IF EXISTS "Users can insert own timelines" ON public.timelines;
CREATE POLICY "Users can insert own timelines" ON public.timelines FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = timelines.project_id AND p.user_id = auth.uid()));

