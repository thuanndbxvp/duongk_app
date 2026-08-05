CREATE TABLE IF NOT EXISTS public.voice_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    sample_audio_url TEXT NOT NULL,
    status TEXT DEFAULT 'ready',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- RLS
ALTER TABLE public.voice_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own voice profiles"
ON public.voice_profiles FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own voice profiles"
ON public.voice_profiles FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own voice profiles"
ON public.voice_profiles FOR DELETE
USING (auth.uid() = user_id);
