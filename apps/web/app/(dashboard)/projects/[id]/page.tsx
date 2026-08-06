'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';

interface Project {
  id: string;
  mode: string;
  status: string;
  approval_state: string;
  brief?: {
    topic: string;
    audience: string;
    language: string;
    duration_target_seconds: number;
    aspect_ratio: string;
    tone: string;
    visual_style: string;
  };
  created_at: string;
  updated_at: string;
}

export default function ProjectWorkspacePage() {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`/api/projects/${id}`)
      .then((res) => {
        if (!res.ok) throw new Error('Project not found');
        return res.json();
      })
      .then((data) => setProject(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-12 text-center">
        <div className="animate-pulse text-[var(--fg-secondary)]">Đang tải project…</div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="max-w-4xl mx-auto py-12 text-center">
        <h2 className="text-xl font-bold text-[var(--danger)]">Project không tìm thấy</h2>
        <p className="text-[var(--fg-secondary)] mt-2">{error || 'Có lỗi xảy ra'}</p>
        <a href="/projects/new" className="inline-block mt-4 text-[var(--brand-400)] hover:underline">
          ← Tạo project mới
        </a>
      </div>
    );
  }
  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-up">
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
            project.status === 'approved' ? 'bg-green-500/20 text-green-400' :
            project.status === 'draft' ? 'bg-blue-500/20 text-blue-400' :
            'bg-gray-500/20 text-gray-400'
          }`}>{project.status}</span>
          <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
            project.mode === 'blank' ? 'bg-purple-500/20 text-purple-400' : 'bg-orange-500/20 text-orange-400'
          }`}>{project.mode === 'blank' ? 'Blank' : 'Clone Channel'}</span>
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          {project.brief?.topic || 'Untitled Project'}
        </h1>
        <p className="text-[var(--fg-secondary)] text-sm">
          Created: {new Date(project.created_at).toLocaleDateString('vi-VN')}
        </p>
      </div>

      {project.brief && (
        <div className="glass-strong rounded-2xl p-6 space-y-4">
          <h2 className="text-lg font-semibold">Creative Brief</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div><span className="text-[var(--fg-tertiary)]">Đối tượng</span>
              <p className="font-medium">{project.brief.audience}</p></div>
            <div><span className="text-[var(--fg-tertiary)]">Ngôn ngữ</span>
              <p className="font-medium">{project.brief.language}</p></div>
            <div><span className="text-[var(--fg-tertiary)]">Thời lượng</span>
              <p className="font-medium">{Math.floor(project.brief.duration_target_seconds / 60)} phút</p></div>
            <div><span className="text-[var(--fg-tertiary)]">Tỷ lệ</span>
              <p className="font-medium">{project.brief.aspect_ratio}</p></div>
            <div><span className="text-[var(--fg-tertiary)]">Giọng điệu</span>
              <p className="font-medium">{project.brief.tone}</p></div>
            <div><span className="text-[var(--fg-tertiary)]">Phong cách</span>
              <p className="font-medium">{project.brief.visual_style}</p></div>
          </div>
        </div>
      )}

      {/* Stage Timeline */}
      <div className="glass-strong rounded-2xl p-6 space-y-4">
        <h2 className="text-lg font-semibold">Tiến độ</h2>
        <div className="flex items-center gap-2">
          {['draft', 'awaiting_approval', 'approved'].map((stage, i) => {
            const isActive = project.approval_state === stage;
            const isPast = (stage === 'draft') || (stage === 'awaiting_approval' && project.approval_state === 'approved');
            return (
              <div key={stage} className="flex items-center gap-2 flex-1">
                <div className={`h-2 flex-1 rounded-full ${
                  isActive ? 'gradient-bg' : isPast ? 'bg-[var(--brand-500)]/50' : 'bg-white/[0.06]'
                }`} />
                <span className={`text-xs whitespace-nowrap ${isActive ? 'text-white font-medium' : 'text-[var(--fg-tertiary)]'}`}>
                  {stage === 'draft' ? 'Draft' : stage === 'awaiting_approval' ? 'Chờ duyệt' : 'Đã duyệt'}
                </span>
                {i < 2 && <div className="w-4" />}
              </div>
            );
          })}
        </div>
      </div>

      {project.approval_state === 'awaiting_approval' && (
        <div className="flex gap-3">
          <button onClick={async () => {
            await fetch(`/api/projects/${id}/approve`, {
              method: 'POST', headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ decision: 'approved' }),
            });
            window.location.reload();
          }} className="flex-1 h-12 rounded-xl gradient-bg text-white font-semibold text-sm">
            ✅ Approve
          </button>
          <button onClick={async () => {
            await fetch(`/api/projects/${id}/approve`, {
              method: 'POST', headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ decision: 'rejected' }),
            });
            window.location.reload();
          }} className="flex-1 h-12 rounded-xl bg-red-500/20 border border-red-500/30 text-red-400 font-semibold text-sm">
            ❌ Reject
          </button>
        </div>
      )}
    </div>
  );
}

