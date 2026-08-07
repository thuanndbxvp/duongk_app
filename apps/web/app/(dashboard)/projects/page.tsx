'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getAccessToken } from '@/lib/auth';

interface Project {
  id: string;
  name: string;
  status: string;
  approval_state: string;
  mode: string;
  created_at: string;
  updated_at: string;
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/projects')
      .then((r) => r.json())
      .then((data) => {
        if (data.data) {
          setProjects(data.data);
        } else {
          setProjects([]);
        }
      })
      .catch(() => setError('Failed to load projects'))
      .finally(() => setLoading(false));
  }, []);

  const statusColors: Record<string, string> = {
    draft: 'bg-yellow-500/20 text-yellow-400',
    approved: 'bg-green-500/20 text-green-400',
    rejected: 'bg-red-500/20 text-red-400',
    generating: 'bg-blue-500/20 text-blue-400',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
            Projects
          </div>
          <h1 className="text-3xl font-bold mt-2">My Projects</h1>
        </div>
        <Link
          href="/projects/new"
          className="inline-flex items-center gap-2 px-5 h-11 rounded-xl text-sm font-semibold glass border border-[var(--glass-border-strong)] text-[var(--brand-300)] hover:bg-[var(--surface-hover)] hover:text-white transition"
        >
          + New Project
        </Link>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin w-8 h-8 border-2 border-[var(--brand-300)] border-t-transparent rounded-full" />
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400">
          {error}
        </div>
      )}

      {!loading && !error && projects.length === 0 && (
        <div className="text-center py-20">
          <p className="text-[var(--fg-secondary)] mb-4">No projects yet</p>
          <Link
            href="/projects/new"
            className="inline-flex items-center gap-2 px-5 h-11 rounded-xl text-sm font-semibold gradient-bg text-white"
          >
            Create your first project
          </Link>
        </div>
      )}

      {!loading && projects.length > 0 && (
        <div className="grid gap-4">
          {projects.map((project) => (
            <Link
              key={project.id}
              href={`/projects/${project.id}`}
              className="block p-4 rounded-xl glass border border-[var(--glass-border)] hover:bg-[var(--surface-hover)] transition"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">{project.name || 'Untitled Project'}</h3>
                  <p className="text-sm text-[var(--fg-secondary)] mt-1">
                    {new Date(project.created_at).toLocaleDateString('vi-VN')}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[project.status] || 'bg-gray-500/20 text-gray-400'}`}>
                    {project.status}
                  </span>
                  <span className="text-xs text-[var(--fg-tertiary)]">
                    {project.mode}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
