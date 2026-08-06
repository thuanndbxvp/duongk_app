-- ============================================================
-- Migration: 0033_ai_media.sql
-- Purpose: Phase 05 — AI Media, Thumbnail, Watermark Cleanup
-- ============================================================

-- Bảng consent_records: user consent for watermark cleanup
CREATE TABLE IF NOT EXISTS public.consent_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  asset_id uuid NOT NULL REFERENCES public.assets(id) ON DELETE CASCADE,
  consent_type text NOT NULL DEFAULT 'watermark_cleanup',
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'revoked')),
  approved_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (user_id, asset_id, consent_type)
);

CREATE INDEX IF NOT EXISTS idx_consent_records_user ON public.consent_records(user_id);
CREATE INDEX IF NOT EXISTS idx_consent_records_asset ON public.consent_records(asset_id);

ALTER TABLE public.consent_records ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "consent_records_owner" ON public.consent_records;
CREATE POLICY "consent_records_owner" ON public.consent_records FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Bảng project_exports: metadata package cho YouTube
CREATE TABLE IF NOT EXISTS public.project_exports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  version int NOT NULL DEFAULT 1,
  title text NOT NULL DEFAULT '',
  description text NOT NULL DEFAULT '',
  tags text[] NOT NULL DEFAULT '{}',
  chapters jsonb NOT NULL DEFAULT '[]'::jsonb,
  hashtags text[] NOT NULL DEFAULT '{}',
  thumbnail_asset_id uuid NULL REFERENCES public.assets(id),
  srt_track_id uuid NULL REFERENCES public.subtitle_tracks(id),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (project_id, version)
);

CREATE INDEX IF NOT EXISTS idx_project_exports_project ON public.project_exports(project_id);

ALTER TABLE public.project_exports ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "project_exports_owner" ON public.project_exports;
CREATE POLICY "project_exports_owner" ON public.project_exports FOR ALL
  USING (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = project_exports.project_id AND p.user_id = auth.uid()))
  WITH CHECK (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = project_exports.project_id AND p.user_id = auth.uid()));

-- Bảng thumbnail_candidates: AI-generated thumbnails cho project
CREATE TABLE IF NOT EXISTS public.thumbnail_candidates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  asset_id uuid NOT NULL REFERENCES public.assets(id) ON DELETE CASCADE,
  score float NULL,
  provider text NOT NULL,
  selected boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_thumbnail_candidates_project ON public.thumbnail_candidates(project_id);

ALTER TABLE public.thumbnail_candidates ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "thumbnail_candidates_owner" ON public.thumbnail_candidates;
CREATE POLICY "thumbnail_candidates_owner" ON public.thumbnail_candidates FOR ALL
  USING (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = thumbnail_candidates.project_id AND p.user_id = auth.uid()))
  WITH CHECK (EXISTS (SELECT 1 FROM public.projects p WHERE p.id = thumbnail_candidates.project_id AND p.user_id = auth.uid()));
