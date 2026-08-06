-- ============================================================
-- Migration: 0035_channel_intel_routing.sql
-- Purpose: Phase 08 — Channel Intelligence routing + enhanced features
-- ============================================================

-- Add routing config entries for community intelligence
INSERT INTO public.service_routing_config (feature, primary_provider, fallback_chain, enabled_providers, cost_per_call_usd)
VALUES
  ('comment_intel', 'youtube_data_api', ARRAY['mock']::TEXT[],
   '{"youtube_data_api":true,"mock":true}'::jsonb,
   '{"youtube_data_api":0.001}'::jsonb),
  ('topic_cluster', 'hdbscan', ARRAY['mock_keyword']::TEXT[],
   '{"hdbscan":true,"mock_keyword":true}'::jsonb,
   '{"hdbscan":0.002,"mock_keyword":0.0}'::jsonb),
  ('trend_provider', 'google_trends_serpapi', ARRAY['mock']::TEXT[],
   '{"google_trends_serpapi":true,"mock":true}'::jsonb,
   '{"google_trends_serpapi":0.005,"mock":0.0}'::jsonb)
ON CONFLICT (feature) DO NOTHING;
