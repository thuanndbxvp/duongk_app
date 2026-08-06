-- ============================================================
-- Migration: 0037_batch_production.sql
-- Purpose: Phase 10 — Batch Production, Cost Estimation, Provider Health
-- ============================================================

-- Bảng batch_runs: root batch entity
CREATE TABLE IF NOT EXISTS public.batch_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name text NOT NULL DEFAULT '',
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'estimated', 'approved', 'running', 'completed', 'partial', 'cancelled', 'failed')),
  total_items int NOT NULL DEFAULT 0,
  succeeded_items int NOT NULL DEFAULT 0,
  failed_items int NOT NULL DEFAULT 0,
  total_cost_estimate int NOT NULL DEFAULT 0,
  total_cost_actual int NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_batch_runs_owner ON public.batch_runs(owner_id);
CREATE INDEX IF NOT EXISTS idx_batch_runs_status ON public.batch_runs(status);

-- Bảng batch_items: per-item trong batch
CREATE TABLE IF NOT EXISTS public.batch_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  batch_id uuid NOT NULL REFERENCES public.batch_runs(id) ON DELETE CASCADE,
  project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  item_index int NOT NULL DEFAULT 0,
  task_type text NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'success', 'failed', 'skipped')),
  provider text NULL,
  fallback_used boolean NOT NULL DEFAULT false,
  retry_count int NOT NULL DEFAULT 0,
  error_message text NULL,
  cost_estimate int NOT NULL DEFAULT 0,
  cost_actual int NOT NULL DEFAULT 0,
  started_at timestamptz NULL,
  finished_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (batch_id, project_id, task_type)
);

CREATE INDEX IF NOT EXISTS idx_batch_items_batch ON public.batch_items(batch_id);

-- Bảng provider_health_snapshots
CREATE TABLE IF NOT EXISTS public.provider_health_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider text NOT NULL,
  is_healthy boolean NOT NULL DEFAULT false,
  quota_remaining int NULL,
  latency_ms int NULL,
  error_message text NULL,
  captured_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_provider_health_provider ON public.provider_health_snapshots(provider, captured_at DESC);
-- ============================================================
-- RLS Policies
-- ============================================================
ALTER TABLE public.batch_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.batch_items ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "owner_all" ON public.batch_runs;
CREATE POLICY "owner_all" ON public.batch_runs FOR ALL USING (auth.uid() = owner_id) WITH CHECK (auth.uid() = owner_id);

DROP POLICY IF EXISTS "owner_via_batch" ON public.batch_items;
CREATE POLICY "owner_via_batch" ON public.batch_items FOR ALL
  USING (EXISTS (SELECT 1 FROM public.batch_runs br WHERE br.id = batch_items.batch_id AND br.owner_id = auth.uid()));

