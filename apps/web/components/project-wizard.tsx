'use client';

import { useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { IconPlus, IconChannels, IconAlert } from '@/components/icons';

type ProjectMode = 'blank' | 'clone_channel';

interface BriefForm {
  topic: string;
  audience: string;
  language: string;
  duration_target_seconds: number;
  aspect_ratio: string;
  tone: string;
  visual_style: string;
  voice_profile_id: string;
  music_mood: string;
}

const DEFAULT_BRIEF: BriefForm = {
  topic: '',
  audience: 'general',
  language: 'vi',
  duration_target_seconds: 600,
  aspect_ratio: '16:9',
  tone: 'casual',
  visual_style: 'cinematic',
  voice_profile_id: '',
  music_mood: '',
};

export function ProjectWizard() {
  const router = useRouter();
  const [mode, setMode] = useState<ProjectMode>('blank');
  const [form, setForm] = useState<BriefForm>(DEFAULT_BRIEF);
  const [channelAssistantId, setChannelAssistantId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  function update(field: keyof BriefForm, value: string | number) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (!form.topic || form.topic.length < 3) {
      setError('Topic phải có ít nhất 3 ký tự');
      setLoading(false);
      return;
    }

    if (form.duration_target_seconds > 3600) {
      setError('Thời lượng không được vượt quá 3600 giây (60 phút)');
      setLoading(false);
      return;
    }

    const payload: Record<string, unknown> = {
      mode,
      brief: {
        topic: form.topic,
        audience: form.audience,
        language: form.language,
        duration_target_seconds: form.duration_target_seconds,
        aspect_ratio: form.aspect_ratio,
        tone: form.tone,
        visual_style: form.visual_style,
        voice_profile_id: form.voice_profile_id || null,
        music_mood: form.music_mood || null,
      },
    };

    if (mode === 'clone_channel') {
      if (!channelAssistantId) {
        setError('clone_channel mode yêu cầu channel_assistant_id');
        setLoading(false);
        return;
      }
      payload.channel_assistant_id = channelAssistantId;
    }

    try {
      const res = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data = await res.json();
        router.push(`/projects/${data.id}`);
      } else {
        const err = await res.json();
        setError(err.detail || 'Có lỗi xảy ra khi tạo project');
      }
    } catch {
      setError('Không thể kết nối đến server');
    }
    setLoading(false);
  }
  return (
    <div className="max-w-2xl mx-auto space-y-8 animate-fade-up">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass text-xs font-medium text-[var(--brand-300)]">
          <IconPlus size={14} /> New Project
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">Tạo Project Mới</span>
        </h1>
        <p className="text-[var(--fg-secondary)]">
          Tạo project từ chủ đề (blank) hoặc clone phong cách từ channel YouTube.
        </p>
      </div>
      <div className="flex gap-2 p-1 rounded-xl glass-strong">
        {(['blank', 'clone_channel'] as ProjectMode[]).map((m) => (
          <button
            key={m} type="button" onClick={() => setMode(m)}
            className={`flex-1 h-10 rounded-lg text-sm font-medium transition-all ${
              mode === m ? 'gradient-bg text-white shadow-lg' : 'text-[var(--fg-secondary)] hover:text-white'
            }`}
          >
            {m === 'blank' ? '🧠 Blank (Topic)' : '📺 Clone Channel'}
          </button>
        ))}
      </div>
      <form onSubmit={handleSubmit} className="relative glass-strong rounded-2xl p-7 space-y-5 overflow-hidden">
        <div aria-hidden className="pointer-events-none absolute -top-24 -right-24 h-56 w-56 rounded-full bg-[var(--brand-500)] opacity-20 blur-3xl" />

        {mode === 'clone_channel' && (
          <div className="relative space-y-1.5">
            <label className="block text-sm font-medium text-[var(--fg-secondary)]">Channel Assistant ID</label>
            <input type="text" value={channelAssistantId}
              onChange={(e) => setChannelAssistantId(e.target.value)}
              placeholder="UUID của channel assistant" required
              className="w-full h-12 px-4 rounded-xl bg-white/[0.04] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)] focus:outline-none focus:border-[var(--brand-400)] focus:bg-white/[0.06] transition"
            />
          </div>
        )}
        <div className="relative space-y-1.5">
          <label className="block text-sm font-medium text-[var(--fg-secondary)]">Chủ đề (Topic) *</label>
          <input type="text" value={form.topic}
            onChange={(e) => update('topic', e.target.value)}
            placeholder="Ví dụ: Cách tối ưu SEO YouTube 2026"
            required minLength={3} maxLength={500}
            className="w-full h-12 px-4 rounded-xl bg-white/[0.04] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)] focus:outline-none focus:border-[var(--brand-400)] focus:bg-white/[0.06] transition"
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-[var(--fg-secondary)]">Đối tượng</label>
            <input type="text" value={form.audience}
              onChange={(e) => update('audience', e.target.value)}
              placeholder="developers"
              className="w-full h-12 px-4 rounded-xl bg-white/[0.04] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)] focus:outline-none focus:border-[var(--brand-400)] transition"
            />
          </div>
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-[var(--fg-secondary)]">Ngôn ngữ</label>
            <div className="relative">
              <select value={form.language} onChange={(e) => update('language', e.target.value)}
                className="w-full h-12 pl-4 pr-10 rounded-xl bg-white/[0.04] border border-[var(--glass-border)] text-white focus:outline-none focus:border-[var(--brand-400)] focus:bg-white/[0.06] transition appearance-none cursor-pointer">
                <option value="vi" className="bg-[var(--surface)] text-white">Tiếng Việt</option>
                <option value="en" className="bg-[var(--surface)] text-white">English</option>
                <option value="ja" className="bg-[var(--surface)] text-white">日本語</option>
                <option value="ko" className="bg-[var(--surface)] text-white">한국어</option>
              </select>
              <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-[var(--fg-tertiary)]">
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-[var(--fg-secondary)]">Thời lượng (giây)</label>
            <input type="number" value={form.duration_target_seconds}
              onChange={(e) => update('duration_target_seconds', parseInt(e.target.value) || 600)}
              min={1} max={3600}
              className="w-full h-12 px-4 rounded-xl bg-white/[0.04] border border-[var(--glass-border)] text-white focus:outline-none focus:border-[var(--brand-400)] transition"
            />
          </div>
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-[var(--fg-secondary)]">Tỷ lệ khung hình</label>
            <div className="relative">
              <select value={form.aspect_ratio} onChange={(e) => update('aspect_ratio', e.target.value)}
                className="w-full h-12 pl-4 pr-10 rounded-xl bg-white/[0.04] border border-[var(--glass-border)] text-white focus:outline-none focus:border-[var(--brand-400)] focus:bg-white/[0.06] transition appearance-none cursor-pointer">
                <option value="16:9" className="bg-[var(--surface)] text-white">16:9 (YouTube)</option>
                <option value="9:16" className="bg-[var(--surface)] text-white">9:16 (Shorts/TikTok)</option>
                <option value="1:1" className="bg-[var(--surface)] text-white">1:1 (Square)</option>
              </select>
              <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-[var(--fg-tertiary)]">
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-[var(--fg-secondary)]">Giọng điệu</label>
            <div className="relative">
              <select value={form.tone} onChange={(e) => update('tone', e.target.value)}
                className="w-full h-12 pl-4 pr-10 rounded-xl bg-white/[0.04] border border-[var(--glass-border)] text-white focus:outline-none focus:border-[var(--brand-400)] focus:bg-white/[0.06] transition appearance-none cursor-pointer">
                <option value="casual" className="bg-[var(--surface)] text-white">Thân mật</option>
                <option value="professional" className="bg-[var(--surface)] text-white">Chuyên nghiệp</option>
                <option value="humorous" className="bg-[var(--surface)] text-white">Hài hước</option>
                <option value="educational" className="bg-[var(--surface)] text-white">Giáo dục</option>
                <option value="dramatic" className="bg-[var(--surface)] text-white">Kịch tính</option>
              </select>
              <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-[var(--fg-tertiary)]">
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </div>
          </div>
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-[var(--fg-secondary)]">Phong cách hình ảnh</label>
            <div className="relative">
              <select value={form.visual_style} onChange={(e) => update('visual_style', e.target.value)}
                className="w-full h-12 pl-4 pr-10 rounded-xl bg-white/[0.04] border border-[var(--glass-border)] text-white focus:outline-none focus:border-[var(--brand-400)] focus:bg-white/[0.06] transition appearance-none cursor-pointer">
                <option value="cinematic" className="bg-[var(--surface)] text-white">Cinematic</option>
                <option value="minimalist" className="bg-[var(--surface)] text-white">Tối giản</option>
                <option value="animated" className="bg-[var(--surface)] text-white">Hoạt hình</option>
                <option value="documentary" className="bg-[var(--surface)] text-white">Tài liệu</option>
                <option value="vlog" className="bg-[var(--surface)] text-white">Vlog</option>
              </select>
              <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-[var(--fg-tertiary)]">
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-[var(--fg-secondary)]">Voice Profile ID</label>
            <input type="text" value={form.voice_profile_id}
              onChange={(e) => update('voice_profile_id', e.target.value)}
              placeholder="UUID (tuỳ chọn)"
              className="w-full h-12 px-4 rounded-xl bg-white/[0.04] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)] focus:outline-none focus:border-[var(--brand-400)] transition"
            />
          </div>
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-[var(--fg-secondary)]">Nhạc nền (mood)</label>
            <input type="text" value={form.music_mood}
              onChange={(e) => update('music_mood', e.target.value)}
              placeholder="Ví dụ: energetic, calm"
              className="w-full h-12 px-4 rounded-xl bg-white/[0.04] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)] focus:outline-none focus:border-[var(--brand-400)] transition"
            />
          </div>
        </div>
        {error && (
          <div className="flex items-start gap-2 text-sm text-[var(--danger)] p-3 rounded-xl bg-[rgba(248,113,113,0.08)] border border-[rgba(248,113,113,0.2)]">
            <IconAlert size={16} className="mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}
        <button type="submit" disabled={loading}
          className="btn-glow relative w-full h-12 rounded-xl text-sm font-semibold text-white inline-flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed">
          <span className="relative inline-flex items-center justify-center gap-2 gradient-bg rounded-[10px] w-full h-12">
            <IconChannels size={16} />
            {loading ? 'Đang tạo project…' : 'Tạo Project'}
          </span>
        </button>
      </form>
    </div>
  );
}

