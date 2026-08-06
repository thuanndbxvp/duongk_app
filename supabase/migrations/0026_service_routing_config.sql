-- ============================================================
-- Migration: 0026_service_routing_config.sql
-- Purpose: Service routing config (DB-driven, hot-reload qua Redis pub/sub)
-- ============================================================

CREATE TABLE IF NOT EXISTS service_routing_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  feature TEXT NOT NULL UNIQUE,
  primary_provider TEXT NOT NULL,
  fallback_chain TEXT[] NOT NULL DEFAULT '{}',
  enabled_providers JSONB NOT NULL DEFAULT '{}',
  cost_per_call_usd JSONB NOT NULL DEFAULT '{}',
  config_version INT NOT NULL DEFAULT 1,
  updated_by UUID REFERENCES users(id),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_routing_feature ON service_routing_config(feature);

-- Seed default routing for 8 features
INSERT INTO service_routing_config (feature, primary_provider, fallback_chain, enabled_providers, cost_per_call_usd) VALUES
  ('transcript_extract', 'supadata', ARRAY['groq','youtube_transcript_api','openai','modal_whisper']::TEXT[],
   '{"supadata":true,"groq":true,"youtube_transcript_api":true,"openai":true,"modal_whisper":true}'::jsonb,
   '{"supadata":0.001,"groq":0.00067,"youtube_transcript_api":0,"openai":0.006,"modal_whisper":0.006}'::jsonb),
  ('llm_text', 'openai', ARRAY['stali']::TEXT[],
   '{"openai":true,"stali":true}'::jsonb,
   '{"openai":0.005,"stali":0.002}'::jsonb),
  ('embedding', 'cohere', ARRAY['openai']::TEXT[],
   '{"cohere":true,"openai":true}'::jsonb,
   '{"cohere":0.0001,"openai":0.00013}'::jsonb),
  ('emotion_classifier', 'openai', ARRAY[]::TEXT[],
   '{"openai":true}'::jsonb,
   '{"openai":0.0005}'::jsonb),
  ('ffmpeg_render', 'modal_t4', ARRAY['modal_a10g','local_cpu']::TEXT[],
   '{"modal_t4":true,"modal_a10g":true,"local_cpu":true}'::jsonb,
   '{"modal_t4":0.02,"modal_a10g":0.04,"local_cpu":0.0}'::jsonb),
  ('tts', 'modal_omnivoice', ARRAY['elevenlabs','openai_tts']::TEXT[],
   '{"modal_omnivoice":true,"elevenlabs":true,"openai_tts":true}'::jsonb,
   '{"modal_omnivoice":0.008,"elevenlabs":0.018,"openai_tts":0.015}'::jsonb),
  ('thumbnail_vision', 'openai', ARRAY['gemini']::TEXT[],
   '{"openai":true,"gemini":false}'::jsonb,
   '{"openai":0.0075,"gemini":0.0025}'::jsonb),
  ('footage_search', 'pexels', ARRAY['pixabay','unsplash']::TEXT[],
   '{"pexels":true,"pixabay":true,"unsplash":true}'::jsonb,
   '{"pexels":0,"pixabay":0,"unsplash":0}'::jsonb)
ON CONFLICT (feature) DO NOTHING;

-- Trigger: pg_notify khi UPDATE
CREATE OR REPLACE FUNCTION notify_routing_update() RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify('routing:config:update', NEW.feature);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_routing_update ON service_routing_config;
CREATE TRIGGER trigger_routing_update
  AFTER UPDATE ON service_routing_config
  FOR EACH ROW
  WHEN (OLD.* IS DISTINCT FROM NEW.*)
  EXECUTE FUNCTION notify_routing_update();

-- RLS
ALTER TABLE service_routing_config ENABLE ROW LEVEL SECURITY;
-- service_role đọc/ghi; non-service default deny