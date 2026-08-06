-- ============================================================
-- Migration: 0038_character_lab.sql
-- Purpose: Phase 11 — Character & Background Lab
-- ============================================================

-- Bảng character_lab_runs: per-project lab session
CREATE TABLE IF NOT EXISTS public.character_lab_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  style_bible_id uuid NULL REFERENCES public.style_bibles(id) ON DELETE SET NULL,
  style_bible_version int NULL,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'generating', 'ready', 'approved', 'superseded')),
  cost_estimate int NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (project_id)
);

CREATE INDEX IF NOT EXISTS idx_lab_runs_project ON public.character_lab_runs(project_id);

-- Bảng character_anchors: generated character references
CREATE TABLE IF NOT EXISTS public.character_anchors (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lab_run_id uuid NOT NULL REFERENCES public.character_lab_runs(id) ON DELETE CASCADE,
  character_name text NOT NULL,
  asset_id uuid NULL REFERENCES public.assets(id) ON DELETE SET NULL,
  provider text NOT NULL,
  anchor_strength float NOT NULL DEFAULT 0.5 CHECK (anchor_strength >= 0 AND anchor_strength <= 1),
  regenerate_count int NOT NULL DEFAULT 0,
  is_approved boolean NOT NULL DEFAULT false,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (lab_run_id, character_name)
);

CREATE INDEX IF NOT EXISTS idx_character_anchors_lab ON public.character_anchors(lab_run_id);

-- Bảng background_anchors: generated background references
CREATE TABLE IF NOT EXISTS public.background_anchors (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lab_run_id uuid NOT NULL REFERENCES public.character_lab_runs(id) ON DELETE CASCADE,
  background_name text NOT NULL DEFAULT 'default',
  asset_id uuid NULL REFERENCES public.assets(id) ON DELETE SET NULL,
  provider text NOT NULL,
  regenerate_count int NOT NULL DEFAULT 0,
  is_approved boolean NOT NULL DEFAULT false,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (lab_run_id, background_name)
);

CREATE INDEX IF NOT EXISTS idx_background_anchors_lab ON public.background_anchors(lab_run_id);

-- Bảng scene_anchor_bindings: scene → anchor mapping
CREATE TABLE IF NOT EXISTS public.scene_anchor_bindings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scene_id uuid NOT NULL REFERENCES public.project_scenes(id) ON DELETE CASCADE,
  character_anchor_id uuid NULL REFERENCES public.character_anchors(id) ON DELETE SET NULL,
  background_anchor_id uuid NULL REFERENCES public.background_anchors(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (scene_id)
);

CREATE INDEX IF NOT EXISTS idx_scene_anchor_bindings_scene ON public.scene_anchor_bindings(scene_id);

-- Bảng lab_approval_evidence: audit log
CREATE TABLE IF NOT EXISTS public.lab_approval_evidence (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lab_run_id uuid NOT NULL REFERENCES public.character_lab_runs(id) ON DELETE CASCADE,
  approved_by uuid NOT NULL REFERENCES auth.users(id),
  coverage_pct float NOT NULL DEFAULT 1.0,
  decision text NOT NULL DEFAULT 'approved',
  created_at timestamptz NOT NULL DEFAULT now()
);
-- ============================================================
-- RLS Policies (via project ownership)
-- ============================================================
ALTER TABLE public.character_lab_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.character_anchors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.background_anchors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scene_anchor_bindings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lab_approval_evidence ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "owner_via_project" ON public.character_lab_runs;
CREATE POLICY "owner_via_project" ON public.character_lab_runs FOR ALL
  USING (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = character_lab_runs.project_id AND p.user_id = auth.uid()));

DROP POLICY IF EXISTS "owner_via_lab_project" ON public.character_anchors;
CREATE POLICY "owner_via_lab_project" ON public.character_anchors FOR ALL
  USING (EXISTS (SELECT 1 FROM public.character_lab_runs lr JOIN public.projects p ON p.id = lr.project_id WHERE lr.id = character_anchors.lab_run_id AND p.user_id = auth.uid()));

DROP POLICY IF EXISTS "owner_via_lab_project" ON public.background_anchors;
CREATE POLICY "owner_via_lab_project" ON public.background_anchors FOR ALL
  USING (EXISTS (SELECT 1 FROM public.character_lab_runs lr JOIN public.projects p ON p.id = lr.project_id WHERE lr.id = background_anchors.lab_run_id AND p.user_id = auth.uid()));

DROP POLICY IF EXISTS "owner_via_scene_project" ON public.scene_anchor_bindings;
CREATE POLICY "owner_via_scene_project" ON public.scene_anchor_bindings FOR ALL
  USING (EXISTS (SELECT 1 FROM public.project_scenes ps JOIN public.projects p ON p.id = ps.project_id WHERE ps.id = scene_anchor_bindings.scene_id AND p.user_id = auth.uid()));

DROP POLICY IF EXISTS "owner_via_lab_project" ON public.lab_approval_evidence;
CREATE POLICY "owner_via_lab_project" ON public.lab_approval_evidence FOR ALL
  USING (EXISTS (SELECT 1 FROM public.character_lab_runs lr JOIN public.projects p ON p.id = lr.project_id WHERE lr.id = lab_approval_evidence.lab_run_id AND p.user_id = auth.uid()));

