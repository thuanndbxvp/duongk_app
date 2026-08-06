-- ============================================================
-- Migration: 0032_render_jobs.sql
-- Purpose: Phase 04 — FFmpeg Render & Export
-- ============================================================

CREATE TABLE IF NOT EXISTS public.render_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  job_type text NOT NULL CHECK (job_type IN ('draft', 'final')),
  cancel_requested boolean NOT NULL DEFAULT false,
  worker_task_id text NULL,
  output_asset_id uuid NULL REFERENCES public.assets(id) ON DELETE SET NULL,
  render_config jsonb NOT NULL DEFAULT '{}'::jsonb,
  error_code text NULL,
  error_message text NULL,
  retry_count int NOT NULL DEFAULT 0,
  started_at timestamptz NULL,
  finished_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'success', 'failed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_render_jobs_project_status ON public.render_jobs(project_id, status);

ALTER TABLE public.render_jobs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "render_jobs_owner_all" ON public.render_jobs;
CREATE POLICY "render_jobs_owner_all" ON public.render_jobs
  FOR ALL
  USING (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = render_jobs.project_id AND p.user_id = auth.uid()))
  WITH CHECK (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = render_jobs.project_id AND p.user_id = auth.uid()));
