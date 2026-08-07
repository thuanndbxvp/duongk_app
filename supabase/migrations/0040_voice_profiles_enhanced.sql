-- ============================================================
-- Migration: 0040_voice_profiles_enhanced.sql
-- Purpose: Tier 1 P0 — Add missing columns to voice_profiles
--          Supports multi-provider voice cloning
-- ============================================================

-- Add missing columns
ALTER TABLE IF EXISTS public.voice_profiles
ADD COLUMN IF NOT EXISTS provider TEXT DEFAULT 'omnivoice',
ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'vi-VN',
ADD COLUMN IF NOT EXISTS gender TEXT DEFAULT 'male',
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now());

-- Add index for user lookups
CREATE INDEX IF NOT EXISTS idx_voice_profiles_user_id ON public.voice_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_profiles_provider ON public.voice_profiles(provider);

-- Create trigger for auto-updating updated_at
CREATE OR REPLACE FUNCTION public.update_voice_profiles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_voice_profiles_updated_at ON public.voice_profiles;
CREATE TRIGGER trg_voice_profiles_updated_at
    BEFORE UPDATE ON public.voice_profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_voice_profiles_updated_at();

-- Update existing RLS policy to be more permissive (update)
DROP POLICY IF EXISTS "Users can update their own voice profiles" ON public.voice_profiles;
CREATE POLICY "Users can update their own voice profiles"
ON public.voice_profiles FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Add CHECK constraint for valid providers
ALTER TABLE IF EXISTS public.voice_profiles
DROP CONSTRAINT IF EXISTS valid_provider;
ALTER TABLE IF EXISTS public.voice_profiles
ADD CONSTRAINT valid_provider
CHECK (provider IN ('omnivoice', 'elevenlabs', 'google_cloud_tts'));

-- Add CHECK constraint for valid languages
ALTER TABLE IF EXISTS public.voice_profiles
DROP CONSTRAINT IF EXISTS valid_language;
ALTER TABLE IF EXISTS public.voice_profiles
ADD CONSTRAINT valid_language
CHECK (language IN ('vi-VN', 'en-US', 'en-GB', 'ja-JP', 'ko-KR', 'zh-CN', 'fr-FR'));

-- Add CHECK constraint for valid genders
ALTER TABLE IF EXISTS public.voice_profiles
DROP CONSTRAINT IF EXISTS valid_gender;
ALTER TABLE IF EXISTS public.voice_profiles
ADD CONSTRAINT valid_gender
CHECK (gender IN ('male', 'female', 'neutral'));
