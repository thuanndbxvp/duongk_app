-- ============================================================
-- Migration: 0030_users_full_name.sql
-- Purpose: Add full_name column to users (used by admin create-user form)
-- Note: Numbered 0030 because 0029 is taken by projects_foundation.sql
-- ============================================================

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS full_name TEXT;

-- Backfill from auth metadata for existing users
UPDATE users u
SET full_name = COALESCE(
  u.full_name,
  (SELECT au.raw_user_meta_data->>'full_name'
   FROM auth.users au
   WHERE au.id = u.id)
)
WHERE full_name IS NULL;

-- Notify PostgREST to refresh schema cache
NOTIFY pgrst, 'reload schema';