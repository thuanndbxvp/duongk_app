-- ============================================================
-- Migration: 0034_channel_intel.sql
-- Purpose: Phase 06 — Channel Intelligence (feedback loop)
-- ============================================================

-- Channel profile versions (versioned persona)
CREATE TABLE IF NOT EXISTS public.channel_profile_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_assistant_id uuid NOT NULL REFERENCES public.channel_assistants(id) ON DELETE CASCADE,
  version int NOT NULL DEFAULT 1,
  audience text NOT NULL DEFAULT '',
  editorial_rules jsonb NOT NULL DEFAULT '[]'::jsonb,
  voice_profile_id uuid NULL REFERENCES public.voice_profiles(id),
  visual_style text NOT NULL DEFAULT '',
  thumbnail_rules jsonb NOT NULL DEFAULT '[]'::jsonb,
  forbidden_claims text[] NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (channel_assistant_id, version)
);

CREATE INDEX IF NOT EXISTS idx_channel_profile_versions_assistant ON public.channel_profile_versions(channel_assistant_id);

-- Comment clusters (HDBSCAN results)
CREATE TABLE IF NOT EXISTS public.comment_clusters (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_assistant_id uuid NOT NULL REFERENCES public.channel_assistants(id) ON DELETE CASCADE,
  topic_label text NOT NULL,
  size int NOT NULL DEFAULT 0,
  sentiment_score float NULL,
  keywords text[] NOT NULL DEFAULT '{}',
  representative_comment_ids text[] NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_comment_clusters_assistant ON public.comment_clusters(channel_assistant_id);

-- Insight items (evidence-backed)
CREATE TABLE IF NOT EXISTS public.insight_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_assistant_id uuid NOT NULL REFERENCES public.channel_assistants(id) ON DELETE CASCADE,
  cluster_id uuid NULL REFERENCES public.comment_clusters(id) ON DELETE SET NULL,
  title text NOT NULL,
  body text NOT NULL,
  evidence_comment_ids text[] NOT NULL DEFAULT '{}',
  opportunity_score float NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'applied')),
  source_project_id uuid NULL REFERENCES public.projects(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_insight_items_assistant ON public.insight_items(channel_assistant_id);
CREATE INDEX IF NOT EXISTS idx_insight_items_status ON public.insight_items(status);

-- Insight outcomes (approved → project tracking)
CREATE TABLE IF NOT EXISTS public.insight_outcomes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  insight_id uuid NOT NULL REFERENCES public.insight_items(id) ON DELETE CASCADE,
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE SET NULL,
  outcome_type text NOT NULL DEFAULT 'project_created',
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Comment ingest batches
CREATE TABLE IF NOT EXISTS public.comment_ingest_batches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_assistant_id uuid NOT NULL REFERENCES public.channel_assistants(id) ON DELETE CASCADE,
  video_ids text[] NOT NULL DEFAULT '{}',
  total_fetched int NOT NULL DEFAULT 0,
  page_token text NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'success', 'failed', 'partial')),
  error_message text NULL,
  started_at timestamptz NULL,
  finished_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_comment_ingest_batches_assistant ON public.comment_ingest_batches(channel_assistant_id);
-- ============================================================
-- RLS Policies (via channel_assistants.user_id)
-- ============================================================
ALTER TABLE public.channel_profile_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.comment_clusters ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.insight_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.insight_outcomes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.comment_ingest_batches ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "owner_via_assistant" ON public.channel_profile_versions;
CREATE POLICY "owner_via_assistant" ON public.channel_profile_versions FOR ALL
  USING (EXISTS (SELECT 1 FROM public.channel_assistants ca WHERE ca.id = channel_profile_versions.channel_assistant_id AND ca.user_id = auth.uid()));

DROP POLICY IF EXISTS "owner_via_assistant" ON public.comment_clusters;
CREATE POLICY "owner_via_assistant" ON public.comment_clusters FOR ALL
  USING (EXISTS (SELECT 1 FROM public.channel_assistants ca WHERE ca.id = comment_clusters.channel_assistant_id AND ca.user_id = auth.uid()));

DROP POLICY IF EXISTS "owner_via_assistant" ON public.insight_items;
CREATE POLICY "owner_via_assistant" ON public.insight_items FOR ALL
  USING (EXISTS (SELECT 1 FROM public.channel_assistants ca WHERE ca.id = insight_items.channel_assistant_id AND ca.user_id = auth.uid()));

DROP POLICY IF EXISTS "owner_via_assistant" ON public.insight_outcomes;
CREATE POLICY "owner_via_assistant" ON public.insight_outcomes FOR ALL
  USING (EXISTS (SELECT 1 FROM public.insight_items ii JOIN public.channel_assistants ca ON ca.id = ii.channel_assistant_id WHERE ii.id = insight_outcomes.insight_id AND ca.user_id = auth.uid()));

DROP POLICY IF EXISTS "owner_via_assistant" ON public.comment_ingest_batches;
CREATE POLICY "owner_via_assistant" ON public.comment_ingest_batches FOR ALL
  USING (EXISTS (SELECT 1 FROM public.channel_assistants ca WHERE ca.id = comment_ingest_batches.channel_assistant_id AND ca.user_id = auth.uid()));

