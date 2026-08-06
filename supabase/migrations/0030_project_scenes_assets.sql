-- ============================================================
-- Migration: 0030_project_scenes_assets.sql
-- Purpose: Phase 02 — Scene Studio, Asset Management & Stock Search
-- Creates project_scenes, assets, asset_variants, scene_assets
-- ============================================================

-- Bảng project_scenes: canonical scene store per project
CREATE TABLE IF NOT EXISTS public.project_scenes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  scene_id text NOT NULL,
  scene_index int NOT NULL,
  schema_version smallint NOT NULL DEFAULT 1,
  narration text NOT NULL DEFAULT '',
  visual_description text NOT NULL DEFAULT '',
  image_prompt text NOT NULL DEFAULT '',
  video_prompt text NOT NULL DEFAULT '',
  asset_type text NOT NULL DEFAULT 'image' CHECK (asset_type IN ('image', 'video')),
  estimated_duration numeric(6,2) NOT NULL DEFAULT 0,
  characters jsonb NOT NULL DEFAULT '[]'::jsonb,
  background text NOT NULL DEFAULT '',
  continuity_references jsonb NOT NULL DEFAULT '[]'::jsonb,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'ready', 'rendered', 'failed')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (project_id, scene_id)
);

CREATE INDEX IF NOT EXISTS idx_project_scenes_project ON public.project_scenes(project_id, scene_index);
CREATE INDEX IF NOT EXISTS idx_project_scenes_scene_id ON public.project_scenes(scene_id);

-- Trigger auto-update updated_at cho project_scenes
CREATE OR REPLACE FUNCTION public.update_project_scenes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_project_scenes_updated_at ON public.project_scenes;
CREATE TRIGGER trg_project_scenes_updated_at
  BEFORE UPDATE ON public.project_scenes
  FOR EACH ROW EXECUTE FUNCTION public.update_project_scenes_updated_at();

-- Bảng assets: global asset registry (user-scoped)
CREATE TABLE IF NOT EXISTS public.assets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  source text NOT NULL CHECK (source IN ('upload', 'pexels', 'local_placeholder', 'ai_generated', 'gemini', 'nanobanana', 'flux', 'sdxl')),
  provider_id text NULL,
  storage_key text NOT NULL,
  mime_type text NOT NULL,
  size_bytes bigint NOT NULL CHECK (size_bytes > 0),
  width int NULL,
  height int NULL,
  duration_seconds numeric(10,3) NULL,
  checksum text NOT NULL,
  license jsonb NOT NULL DEFAULT '{}'::jsonb,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  status text NOT NULL DEFAULT 'ready' CHECK (status IN ('uploading', 'ready', 'processing', 'failed', 'deleted')),
  deleted_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (source, provider_id)
);

CREATE INDEX IF NOT EXISTS idx_assets_owner ON public.assets(owner_id);
CREATE INDEX IF NOT EXISTS idx_assets_source ON public.assets(source);
CREATE INDEX IF NOT EXISTS idx_assets_status ON public.assets(status);
CREATE INDEX IF NOT EXISTS idx_assets_checksum ON public.assets(checksum);

-- Trigger auto-update updated_at cho assets
DROP TRIGGER IF EXISTS trg_assets_updated_at ON public.assets;
CREATE TRIGGER trg_assets_updated_at
  BEFORE UPDATE ON public.assets
  FOR EACH ROW EXECUTE FUNCTION public.update_projects_updated_at();
-- Bảng asset_variants: variant tracking (original, preview, processed)
CREATE TABLE IF NOT EXISTS public.asset_variants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id uuid NOT NULL REFERENCES public.assets(id) ON DELETE CASCADE,
  variant_kind text NOT NULL CHECK (variant_kind IN ('original', 'preview', 'normalized', 'upscaled', 'processed')),
  storage_key text NOT NULL,
  mime_type text NOT NULL,
  size_bytes bigint NOT NULL CHECK (size_bytes > 0),
  width int NULL,
  height int NULL,
  duration_seconds numeric(10,3) NULL,
  processed_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (asset_id, variant_kind)
);

CREATE INDEX IF NOT EXISTS idx_asset_variants_asset ON public.asset_variants(asset_id);

-- Bảng scene_assets: n-n binding giữa scenes và assets
CREATE TABLE IF NOT EXISTS public.scene_assets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scene_id uuid NOT NULL REFERENCES public.project_scenes(id) ON DELETE CASCADE,
  asset_id uuid NOT NULL REFERENCES public.assets(id) ON DELETE CASCADE,
  position int NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (scene_id, asset_id)
);

CREATE INDEX IF NOT EXISTS idx_scene_assets_scene ON public.scene_assets(scene_id);
CREATE INDEX IF NOT EXISTS idx_scene_assets_asset ON public.scene_assets(asset_id);

-- ============================================================
-- RLS Policies
-- ============================================================
ALTER TABLE public.project_scenes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.asset_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scene_assets ENABLE ROW LEVEL SECURITY;

-- project_scenes: owner qua project
DROP POLICY IF EXISTS "Users can view own project scenes" ON public.project_scenes;
CREATE POLICY "Users can view own project scenes" ON public.project_scenes FOR SELECT
  USING (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = project_scenes.project_id AND p.user_id = auth.uid()));

DROP POLICY IF EXISTS "Users can insert own project scenes" ON public.project_scenes;
CREATE POLICY "Users can insert own project scenes" ON public.project_scenes FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = project_scenes.project_id AND p.user_id = auth.uid()));

DROP POLICY IF EXISTS "Users can update own project scenes" ON public.project_scenes;
CREATE POLICY "Users can update own project scenes" ON public.project_scenes FOR UPDATE
  USING (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = project_scenes.project_id AND p.user_id = auth.uid()));

DROP POLICY IF EXISTS "Users can delete own project scenes" ON public.project_scenes;
CREATE POLICY "Users can delete own project scenes" ON public.project_scenes FOR DELETE
  USING (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = project_scenes.project_id AND p.user_id = auth.uid()));

-- assets: owner trực tiếp
DROP POLICY IF EXISTS "Users can view own assets" ON public.assets;
CREATE POLICY "Users can view own assets" ON public.assets FOR SELECT USING (auth.uid() = owner_id);

DROP POLICY IF EXISTS "Users can insert own assets" ON public.assets;
CREATE POLICY "Users can insert own assets" ON public.assets FOR INSERT WITH CHECK (auth.uid() = owner_id);

DROP POLICY IF EXISTS "Users can update own assets" ON public.assets;
CREATE POLICY "Users can update own assets" ON public.assets FOR UPDATE USING (auth.uid() = owner_id);

DROP POLICY IF EXISTS "Users can delete own assets" ON public.assets;
CREATE POLICY "Users can delete own assets" ON public.assets FOR DELETE USING (auth.uid() = owner_id);

-- asset_variants: owner qua asset
DROP POLICY IF EXISTS "Users can view own asset variants" ON public.asset_variants;
CREATE POLICY "Users can view own asset variants" ON public.asset_variants FOR SELECT
  USING (EXISTS (SELECT 1 FROM public.assets a WHERE a.id = asset_variants.asset_id AND a.owner_id = auth.uid()));

DROP POLICY IF EXISTS "Users can insert own asset variants" ON public.asset_variants;
CREATE POLICY "Users can insert own asset variants" ON public.asset_variants FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM public.assets a WHERE a.id = asset_variants.asset_id AND a.owner_id = auth.uid()));

-- scene_assets: owner qua scene → project
DROP POLICY IF EXISTS "Users can view own scene assets" ON public.scene_assets;
CREATE POLICY "Users can view own scene assets" ON public.scene_assets FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM public.project_scenes ps
    JOIN public.projects p ON p.id = ps.project_id
    WHERE ps.id = scene_assets.scene_id AND p.user_id = auth.uid()
  ));

DROP POLICY IF EXISTS "Users can insert own scene assets" ON public.scene_assets;
CREATE POLICY "Users can insert own scene assets" ON public.scene_assets FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM public.project_scenes ps
    JOIN public.projects p ON p.id = ps.project_id
    WHERE ps.id = scene_assets.scene_id AND p.user_id = auth.uid()
  ));

DROP POLICY IF EXISTS "Users can delete own scene assets" ON public.scene_assets;
CREATE POLICY "Users can delete own scene assets" ON public.scene_assets FOR DELETE
  USING (EXISTS (
    SELECT 1 FROM public.project_scenes ps
    JOIN public.projects p ON p.id = ps.project_id
    WHERE ps.id = scene_assets.scene_id AND p.user_id = auth.uid()
  ));

