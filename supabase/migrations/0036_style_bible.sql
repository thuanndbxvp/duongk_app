-- ============================================================
-- Migration: 0036_style_bible.sql
-- Purpose: Phase 09 — Style Bible, Character Refs, Design System
-- ============================================================

-- Bảng style_bibles: root entity
CREATE TABLE IF NOT EXISTS public.style_bibles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name text NOT NULL,
  description text NOT NULL DEFAULT '',
  visual_palette jsonb NOT NULL DEFAULT '{}'::jsonb,
  lens_preference text NOT NULL DEFAULT '',
  motion_style text NOT NULL DEFAULT '',
  negative_prompt text NOT NULL DEFAULT '',
  version int NOT NULL DEFAULT 1,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_style_bibles_owner ON public.style_bibles(owner_id);

-- Bảng style_bible_versions: version history
CREATE TABLE IF NOT EXISTS public.style_bible_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  bible_id uuid NOT NULL REFERENCES public.style_bibles(id) ON DELETE CASCADE,
  version int NOT NULL,
  snapshot jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (bible_id, version)
);

CREATE INDEX IF NOT EXISTS idx_style_bible_versions_bible ON public.style_bible_versions(bible_id, version DESC);

-- Bảng style_bible_assets: character/background references
CREATE TABLE IF NOT EXISTS public.style_bible_assets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  bible_id uuid NOT NULL REFERENCES public.style_bibles(id) ON DELETE CASCADE,
  asset_id uuid NOT NULL REFERENCES public.assets(id) ON DELETE CASCADE,
  ref_type text NOT NULL CHECK (ref_type IN ('character', 'background')),
  anchor_strength float NOT NULL DEFAULT 0.5 CHECK (anchor_strength >= 0 AND anchor_strength <= 1),
  label text NOT NULL DEFAULT '',
  UNIQUE (bible_id, asset_id, ref_type)
);

CREATE INDEX IF NOT EXISTS idx_style_bible_assets_bible ON public.style_bible_assets(bible_id);

-- Bảng scene_style_applications: bible → scene binding
CREATE TABLE IF NOT EXISTS public.scene_style_applications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scene_id uuid NOT NULL REFERENCES public.project_scenes(id) ON DELETE CASCADE,
  bible_id uuid NOT NULL REFERENCES public.style_bibles(id) ON DELETE CASCADE,
  bible_version int NOT NULL,
  merged_prompt text NOT NULL DEFAULT '',
  merged_negative text NOT NULL DEFAULT '',
  fingerprint text NOT NULL,
  applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_scene_style_app_scene ON public.scene_style_applications(scene_id);
-- ============================================================
-- RLS Policies
-- ============================================================
ALTER TABLE public.style_bibles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.style_bible_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.style_bible_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scene_style_applications ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "owner_all" ON public.style_bibles;
CREATE POLICY "owner_all" ON public.style_bibles FOR ALL USING (auth.uid() = owner_id) WITH CHECK (auth.uid() = owner_id);

DROP POLICY IF EXISTS "owner_via_bible" ON public.style_bible_versions;
CREATE POLICY "owner_via_bible" ON public.style_bible_versions FOR ALL
  USING (EXISTS (SELECT 1 FROM public.style_bibles sb WHERE sb.id = style_bible_versions.bible_id AND sb.owner_id = auth.uid()));

DROP POLICY IF EXISTS "owner_via_bible" ON public.style_bible_assets;
CREATE POLICY "owner_via_bible" ON public.style_bible_assets FOR ALL
  USING (EXISTS (SELECT 1 FROM public.style_bibles sb WHERE sb.id = style_bible_assets.bible_id AND sb.owner_id = auth.uid()));

DROP POLICY IF EXISTS "owner_via_scene_project" ON public.scene_style_applications;
CREATE POLICY "owner_via_scene_project" ON public.scene_style_applications FOR ALL
  USING (EXISTS (
    SELECT 1 FROM public.project_scenes ps
    JOIN public.projects p ON p.id = ps.project_id
    WHERE ps.id = scene_style_applications.scene_id AND p.user_id = auth.uid()
  ));

