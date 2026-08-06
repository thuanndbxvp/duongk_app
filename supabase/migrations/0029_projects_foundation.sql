-- ============================================================
-- Migration: 0029_projects_foundation.sql
-- Purpose: Phase 01 — Project foundation & blank project onboarding
-- Creates projects, project_briefs, project_stage_events tables
-- with RLS policies + idempotency support
-- ============================================================

-- Bảng projects: root entity mới
CREATE TABLE IF NOT EXISTS public.projects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  channel_assistant_id uuid NULL REFERENCES public.channel_assistants(id) ON DELETE SET NULL,
  mode text NOT NULL CHECK (mode IN ('blank', 'clone_channel')),
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'awaiting_approval', 'approved', 'rejected', 'archived')),
  approval_state text NOT NULL DEFAULT 'draft' CHECK (approval_state IN ('draft', 'awaiting_approval', 'approved', 'rejected')),
  brief_hash text NOT NULL,
  schema_version smallint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  approved_at timestamptz NULL,
  UNIQUE (user_id, brief_hash)
);

-- Index cho lookup idempotent
CREATE INDEX IF NOT EXISTS idx_projects_user_brief_hash ON public.projects(user_id, brief_hash);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_channel_assistant_id ON public.projects(channel_assistant_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON public.projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON public.projects(created_at DESC);

-- Trigger auto-update updated_at
CREATE OR REPLACE FUNCTION public.update_projects_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_projects_updated_at ON public.projects;
CREATE TRIGGER trg_projects_updated_at
  BEFORE UPDATE ON public.projects
  FOR EACH ROW EXECUTE FUNCTION public.update_projects_updated_at();

-- ============================================================
-- Bảng project_briefs: versioned creative brief
-- ============================================================
CREATE TABLE IF NOT EXISTS public.project_briefs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  version smallint NOT NULL DEFAULT 1,
  topic text NOT NULL,
  audience text NOT NULL DEFAULT 'general',
  language text NOT NULL DEFAULT 'vi',
  duration_target_seconds integer NOT NULL DEFAULT 600 CHECK (duration_target_seconds > 0 AND duration_target_seconds <= 3600),
  aspect_ratio text NOT NULL DEFAULT '16:9',
  tone text NOT NULL DEFAULT 'casual',
  visual_style text NOT NULL DEFAULT 'cinematic',
  voice_profile_id uuid NULL REFERENCES public.voice_profiles(id) ON DELETE SET NULL,
  music_mood text NULL,
  extra jsonb NULL DEFAULT '{}'::jsonb,
  schema_version smallint NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (project_id, version)
);

CREATE INDEX IF NOT EXISTS idx_project_briefs_project_id ON public.project_briefs(project_id);

-- ============================================================
-- Bảng project_stage_events: audit log các stage transition
-- ============================================================
CREATE TABLE IF NOT EXISTS public.project_stage_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  stage text NOT NULL,
  event_type text NOT NULL CHECK (event_type IN ('created', 'submitted', 'approved', 'rejected', 'archived', 'brief_updated')),
  payload jsonb NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_project_stage_events_project_id ON public.project_stage_events(project_id);
CREATE INDEX IF NOT EXISTS idx_project_stage_events_created_at ON public.project_stage_events(created_at DESC);

-- ============================================================
-- RLS Policies cho projects
-- ============================================================
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_briefs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_stage_events ENABLE ROW LEVEL SECURITY;

-- projects: user chỉ thấy project của mình
DROP POLICY IF EXISTS "Users can view own projects" ON public.projects;
CREATE POLICY "Users can view own projects" ON public.projects
  FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own projects" ON public.projects;
CREATE POLICY "Users can insert own projects" ON public.projects
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own projects" ON public.projects;
CREATE POLICY "Users can update own projects" ON public.projects
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own projects" ON public.projects;
CREATE POLICY "Users can delete own projects" ON public.projects
  FOR DELETE
  USING (auth.uid() = user_id);

-- project_briefs: user chỉ thấy brief của project mình sở hữu
DROP POLICY IF EXISTS "Users can view own project briefs" ON public.project_briefs;
CREATE POLICY "Users can view own project briefs" ON public.project_briefs
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.projects p
      WHERE p.id = project_briefs.project_id AND p.user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can insert own project briefs" ON public.project_briefs;
CREATE POLICY "Users can insert own project briefs" ON public.project_briefs
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.projects p
      WHERE p.id = project_briefs.project_id AND p.user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can update own project briefs" ON public.project_briefs;
CREATE POLICY "Users can update own project briefs" ON public.project_briefs
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.projects p
      WHERE p.id = project_briefs.project_id AND p.user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can delete own project briefs" ON public.project_briefs;
CREATE POLICY "Users can delete own project briefs" ON public.project_briefs
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.projects p
      WHERE p.id = project_briefs.project_id AND p.user_id = auth.uid()
    )
  );

-- project_stage_events: user chỉ thấy events của project mình sở hữu
DROP POLICY IF EXISTS "Users can view own project stage events" ON public.project_stage_events;
CREATE POLICY "Users can view own project stage events" ON public.project_stage_events
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.projects p
      WHERE p.id = project_stage_events.project_id AND p.user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can insert own project stage events" ON public.project_stage_events;
CREATE POLICY "Users can insert own project stage events" ON public.project_stage_events
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.projects p
      WHERE p.id = project_stage_events.project_id AND p.user_id = auth.uid()
    )
  );

-- ============================================================
-- RPC: idempotent project lookup
-- ============================================================
CREATE OR REPLACE FUNCTION public.lookup_project_by_brief_hash(
  p_user_id uuid,
  p_brief_hash text
)
RETURNS TABLE(project_id uuid, found boolean) AS $$
BEGIN
  RETURN QUERY
  SELECT p.id, TRUE::boolean
  FROM public.projects p
  WHERE p.user_id = p_user_id AND p.brief_hash = p_brief_hash
  LIMIT 1;

  IF NOT FOUND THEN
    RETURN QUERY SELECT NULL::uuid, FALSE::boolean;
  END IF;
END;
$$ LANGUAGE plpgsql STABLE SECURITY INVOKER;
