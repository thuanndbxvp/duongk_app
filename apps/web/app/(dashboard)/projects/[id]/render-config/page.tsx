'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Select } from '@/components/select';

// =============================================================================
// Types & Schemas
// =============================================================================

const RENDER_CONFIG_SCHEMA = z.object({
  // Video Output
  resolution: z.enum(['1920x1080', '1280x720', '3840x2160', '2560x1440']),
  frame_rate: z.enum(['24', '30', '60']),
  aspect_ratio: z.enum(['16:9', '9:16', '1:1', '4:3']),
  
  // Encoding
  codec: z.enum(['h264', 'h265', 'vp9', 'prores']),
  bitrate: z.enum(['low', 'medium', 'high', 'ultra']),
  audio_codec: z.enum(['aac', 'opus', 'mp3']),
  audio_bitrate: z.enum(['128k', '192k', '256k', '320k']),
  
  // Quality
  quality_preset: z.enum(['fast', 'medium', 'slow', 'high_quality']),
  crf: z.number().min(0).max(51),
  
  // GPU Acceleration
  use_gpu: z.boolean(),
  gpu_encoder: z.enum(['nvenc', 'vaapi', 'videotoolbox', 'software']).optional(),
  
  // Watermark
  watermark_enabled: z.boolean(),
  watermark_position: z.enum(['top-left', 'top-right', 'bottom-left', 'bottom-right', 'center']),
  watermark_opacity: z.number().min(0).max(1),
  
  // Subtitles
  subtitles_enabled: z.boolean(),
  subtitles_language: z.string(),
  subtitles_style: z.object({
    font_size: z.number(),
    font_color: z.string(),
    background_color: z.string().optional(),
  }),
  
  // Audio
  audio_normalization: z.boolean(),
  audio_denoise: z.boolean(),
  volume_level: z.number().min(0).max(2),
  
  // Advanced
  color_grade: z.boolean(),
  sharpen: z.boolean(),
  deinterlace: z.boolean(),
});

type RenderConfig = z.infer<typeof RENDER_CONFIG_SCHEMA>;

const DEFAULT_CONFIG: RenderConfig = {
  resolution: '1920x1080',
  frame_rate: '30',
  aspect_ratio: '16:9',
  codec: 'h264',
  bitrate: 'high',
  audio_codec: 'aac',
  audio_bitrate: '192k',
  quality_preset: 'medium',
  crf: 23,
  use_gpu: true,
  gpu_encoder: 'nvenc',
  watermark_enabled: true,
  watermark_position: 'bottom-right',
  watermark_opacity: 0.7,
  subtitles_enabled: true,
  subtitles_language: 'vi',
  subtitles_style: {
    font_size: 24,
    font_color: '#FFFFFF',
    background_color: '#00000080',
  },
  audio_normalization: true,
  audio_denoise: false,
  volume_level: 1.0,
  color_grade: false,
  sharpen: false,
  deinterlace: false,
};

interface Project {
  id: string;
  render_config?: Partial<RenderConfig> | null;
  brief?: {
    topic?: string;
  };
}

// =============================================================================
// Main Component
// =============================================================================

export default function RenderConfigPage() {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    reset,
    setValue,
    formState: { errors, isDirty },
  } = useForm<RenderConfig>({
    resolver: zodResolver(RENDER_CONFIG_SCHEMA),
    defaultValues: DEFAULT_CONFIG,
  });

  // Watch GPU toggle
  const useGpu = watch('use_gpu');

  // Fetch project
  useEffect(() => {
    fetch(`/api/projects/${id}`)
      .then((res) => res.ok ? res.json() : null)
      .then((data) => {
        if (data) {
          setProject(data);
          if (data.render_config) {
            reset({ ...DEFAULT_CONFIG, ...data.render_config });
          }
        }
      })
      .catch(() => null)
      .finally(() => setLoading(false));
  }, [id, reset]);

  // Save handler
  async function onSubmit(data: RenderConfig) {
    setSaving(true);
    setError(null);
    setSaved(false);

    try {
      const res = await fetch(`/api/projects/${id}/render-config`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Save failed');
      }

      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-12 text-center">
        <div className="animate-pulse text-[var(--fg-secondary)]">Đang tải…</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-up">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <a href={`/projects/${id}`} className="text-sm text-[var(--brand-400)] hover:underline">
            ← Back to Project
          </a>
          <span className="text-[var(--fg-tertiary)]">|</span>
          <span className="text-sm text-[var(--fg-tertiary)]">
            {project?.brief?.topic || `Project ${id}`}
          </span>
        </div>
        <h1 className="text-3xl font-bold tracking-tight">
          <span className="gradient-text">Render Config Editor</span>
        </h1>
        <p className="text-[var(--fg-secondary)]">
          Cấu hình render cho video output. JSONB được lưu vào <code className="text-[var(--brand-300)]">render_jobs.render_config</code>.
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Video Output */}
        <SectionCard title="Video Output" icon="🎬">
          <div className="grid sm:grid-cols-2 gap-4">
            <FormField label="Resolution" error={errors.resolution?.message}>
              <Select
                {...register('resolution')}
                options={[
                  { value: '1920x1080', label: '1920x1080 (Full HD)' },
                  { value: '1280x720', label: '1280x720 (HD)' },
                  { value: '3840x2160', label: '3840x2160 (4K)' },
                  { value: '2560x1440', label: '2560x1440 (2K)' },
                ]}
              />
            </FormField>

            <FormField label="Frame Rate" error={errors.frame_rate?.message}>
              <Select
                {...register('frame_rate')}
                options={[
                  { value: '24', label: '24 fps (Cinematic)' },
                  { value: '30', label: '30 fps (Standard)' },
                  { value: '60', label: '60 fps (Smooth)' },
                ]}
              />
            </FormField>

            <FormField label="Aspect Ratio" error={errors.aspect_ratio?.message}>
              <Select
                {...register('aspect_ratio')}
                options={[
                  { value: '16:9', label: '16:9 (Landscape)' },
                  { value: '9:16', label: '9:16 (Vertical/TikTok)' },
                  { value: '1:1', label: '1:1 (Square)' },
                  { value: '4:3', label: '4:3 (Classic)' },
                ]}
              />
            </FormField>

            <FormField label="Quality Preset" error={errors.quality_preset?.message}>
              <Select
                {...register('quality_preset')}
                options={[
                  { value: 'fast', label: 'Fast (Smaller file)' },
                  { value: 'medium', label: 'Medium (Balanced)' },
                  { value: 'slow', label: 'Slow (Better quality)' },
                  { value: 'high_quality', label: 'High Quality (Largest)' },
                ]}
              />
            </FormField>

            <FormField label="CRF (0-51, lower = better)" error={errors.crf?.message}>
              <input
                type="number"
                {...register('crf', { valueAsNumber: true })}
                min={0}
                max={51}
                className="w-full px-4 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)]"
              />
              <p className="text-xs text-[var(--fg-tertiary)] mt-1">
                Recommended: 18-23 for high quality, 23-28 for smaller files
              </p>
            </FormField>
          </div>
        </SectionCard>

        {/* Encoding */}
        <SectionCard title="Encoding" icon="⚙️">
          <div className="grid sm:grid-cols-2 gap-4">
            <FormField label="Video Codec" error={errors.codec?.message}>
              <Select
                {...register('codec')}
                options={[
                  { value: 'h264', label: 'H.264 (Most compatible)' },
                  { value: 'h265', label: 'H.265/HEVC (Better compression)' },
                  { value: 'vp9', label: 'VP9 (Web optimized)' },
                  { value: 'prores', label: 'ProRes (Professional)' },
                ]}
              />
            </FormField>

            <FormField label="Bitrate" error={errors.bitrate?.message}>
              <Select
                {...register('bitrate')}
                options={[
                  { value: 'low', label: 'Low (~2 Mbps)' },
                  { value: 'medium', label: 'Medium (~5 Mbps)' },
                  { value: 'high', label: 'High (~10 Mbps)' },
                  { value: 'ultra', label: 'Ultra (~20 Mbps)' },
                ]}
              />
            </FormField>

            <FormField label="Audio Codec" error={errors.audio_codec?.message}>
              <Select
                {...register('audio_codec')}
                options={[
                  { value: 'aac', label: 'AAC (Recommended)' },
                  { value: 'opus', label: 'Opus (Web optimized)' },
                  { value: 'mp3', label: 'MP3 (Legacy)' },
                ]}
              />
            </FormField>

            <FormField label="Audio Bitrate" error={errors.audio_bitrate?.message}>
              <Select
                {...register('audio_bitrate')}
                options={[
                  { value: '128k', label: '128 kbps' },
                  { value: '192k', label: '192 kbps' },
                  { value: '256k', label: '256 kbps' },
                  { value: '320k', label: '320 kbps' },
                ]}
              />
            </FormField>
          </div>
        </SectionCard>

        {/* GPU Acceleration */}
        <SectionCard title="GPU Acceleration" icon="🚀">
          <div className="space-y-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                {...register('use_gpu')}
                className="w-5 h-5 rounded border-[var(--glass-border)]"
              />
              <span className="text-sm font-medium">Enable GPU Encoding</span>
            </label>

            {useGpu && (
              <FormField label="GPU Encoder" error={errors.gpu_encoder?.message}>
                <Select
                  {...register('gpu_encoder')}
                  options={[
                    { value: 'nvenc', label: 'NVENC (NVIDIA GPU)' },
                    { value: 'vaapi', label: 'VAAPI (Linux Intel/AMD)' },
                    { value: 'videotoolbox', label: 'VideoToolbox (macOS)' },
                    { value: 'software', label: 'Software (CPU fallback)' },
                  ]}
                />
              </FormField>
            )}
          </div>
        </SectionCard>

        {/* Watermark */}
        <SectionCard title="Watermark" icon="💧">
          <div className="space-y-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                {...register('watermark_enabled')}
                className="w-5 h-5 rounded border-[var(--glass-border)]"
              />
              <span className="text-sm font-medium">Enable Watermark</span>
            </label>

            {watch('watermark_enabled') && (
              <div className="grid sm:grid-cols-2 gap-4">
                <FormField label="Position" error={errors.watermark_position?.message}>
                  <Select
                    {...register('watermark_position')}
                    options={[
                      { value: 'top-left', label: 'Top Left' },
                      { value: 'top-right', label: 'Top Right' },
                      { value: 'bottom-left', label: 'Bottom Left' },
                      { value: 'bottom-right', label: 'Bottom Right' },
                      { value: 'center', label: 'Center' },
                    ]}
                  />
                </FormField>

                <FormField label="Opacity (0-1)" error={errors.watermark_opacity?.message}>
                  <input
                    type="number"
                    {...register('watermark_opacity', { valueAsNumber: true })}
                    min={0}
                    max={1}
                    step={0.1}
                    className="w-full px-4 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)]"
                  />
                </FormField>
              </div>
            )}
          </div>
        </SectionCard>

        {/* Subtitles */}
        <SectionCard title="Subtitles" icon="📝">
          <div className="space-y-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                {...register('subtitles_enabled')}
                className="w-5 h-5 rounded border-[var(--glass-border)]"
              />
              <span className="text-sm font-medium">Enable Subtitles</span>
            </label>

            {watch('subtitles_enabled') && (
              <div className="grid sm:grid-cols-2 gap-4">
                <FormField label="Language" error={errors.subtitles_language?.message}>
                  <input
                    type="text"
                    {...register('subtitles_language')}
                    placeholder="vi, en, ja..."
                    className="w-full px-4 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)]"
                  />
                </FormField>

                <FormField label="Font Size" error={errors.subtitles_style?.font_size?.message}>
                  <input
                    type="number"
                    {...register('subtitles_style.font_size', { valueAsNumber: true })}
                    min={12}
                    max={72}
                    className="w-full px-4 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)]"
                  />
                </FormField>

                <FormField label="Font Color" error={errors.subtitles_style?.font_color?.message}>
                  <input
                    type="color"
                    {...register('subtitles_style.font_color')}
                    className="w-full h-10 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)]"
                  />
                </FormField>
              </div>
            )}
          </div>
        </SectionCard>

        {/* Audio */}
        <SectionCard title="Audio Processing" icon="🔊">
          <div className="space-y-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                {...register('audio_normalization')}
                className="w-5 h-5 rounded border-[var(--glass-border)]"
              />
              <span className="text-sm font-medium">Audio Normalization (LUFS -14)</span>
            </label>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                {...register('audio_denoise')}
                className="w-5 h-5 rounded border-[var(--glass-border)]"
              />
              <span className="text-sm font-medium">Audio Denoise</span>
            </label>

            <FormField label="Volume Level (0-2)" error={errors.volume_level?.message}>
              <input
                type="number"
                {...register('volume_level', { valueAsNumber: true })}
                min={0}
                max={2}
                step={0.1}
                className="w-full px-4 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)]"
              />
            </FormField>
          </div>
        </SectionCard>

        {/* Advanced */}
        <SectionCard title="Advanced" icon="🔧">
          <div className="space-y-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                {...register('color_grade')}
                className="w-5 h-5 rounded border-[var(--glass-border)]"
              />
              <span className="text-sm font-medium">Color Grading</span>
            </label>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                {...register('sharpen')}
                className="w-5 h-5 rounded border-[var(--glass-border)]"
              />
              <span className="text-sm font-medium">Sharpen</span>
            </label>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                {...register('deinterlace')}
                className="w-5 h-5 rounded border-[var(--glass-border)]"
              />
              <span className="text-sm font-medium">Deinterlace</span>
            </label>
          </div>
        </SectionCard>

        {/* Actions */}
        <div className="flex items-center gap-4">
          <button
            type="submit"
            disabled={saving || !isDirty}
            className="px-6 py-3 rounded-xl gradient-bg text-white font-semibold disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Save Configuration'}
          </button>
          
          <button
            type="button"
            onClick={() => reset()}
            disabled={!isDirty}
            className="px-6 py-3 rounded-xl bg-[var(--surface)] border border-[var(--glass-border)] text-sm disabled:opacity-50"
          >
            Reset
          </button>

          {saved && (
            <span className="text-green-400 text-sm">✓ Saved!</span>
          )}

          {error && (
            <span className="text-red-400 text-sm">{error}</span>
          )}
        </div>
      </form>
    </div>
  );
}

// =============================================================================
// Helper Components
// =============================================================================

function SectionCard({ title, icon, children }: { title: string; icon: string; children: React.ReactNode }) {
  return (
    <div className="glass rounded-2xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">{icon}</span>
        <h2 className="text-lg font-semibold">{title}</h2>
      </div>
      {children}
    </div>
  );
}

function FormField({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <label className="text-sm font-medium text-[var(--fg-secondary)]">{label}</label>
      {children}
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}
