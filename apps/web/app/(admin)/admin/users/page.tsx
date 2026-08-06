'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { buildQuery, useArrayFetch } from '@/lib/use-fetch';
import { Select } from '@/components/select';
import { CreateUserModal } from '@/components/create-user-modal';

interface User {
  id: string;
  email: string;
  full_name: string | null;
  credits: number;
  tier: string;
  role: string;
  banned_at: string | null;
  deleted_at: string | null;
  created_at: string;
}

export default function AdminUsersPage() {
  const router = useRouter();
  const [search, setSearch] = useState('');
  const [tierFilter, setTierFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [page, setPage] = useState(1);
  const [showCreate, setShowCreate] = useState(false);
  const [toast, setToast] = useState<{ kind: 'success' | 'error'; msg: string } | null>(null);

  const url = `/api/admin/users${buildQuery({
    page,
    limit: 50,
    q: search,
    tier: tierFilter,
    status: statusFilter,
    role: roleFilter,
  })}`;
  const { data: users, total, loading, refresh } = useArrayFetch<User>(
    url,
    [page, search, tierFilter, statusFilter, roleFilter],
    'users',
  );

  const totalPages = Math.max(1, Math.ceil(total / 50));

  const showToast = (kind: 'success' | 'error', msg: string) => {
    setToast({ kind, msg });
    window.setTimeout(() => setToast(null), 3500);
  };

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          Admin
        </div>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
              <span className="gradient-text">Users</span>
            </h1>
            <p className="text-[var(--fg-secondary)]">{total} users total</p>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="h-9 px-4 rounded-lg bg-[var(--brand-500)] text-sm font-semibold text-white hover:bg-[var(--brand-400)] transition-colors"
          >
            + Create user
          </button>
        </div>
      </div>

      {toast && (
        <div
          className={`rounded-xl px-4 py-3 text-sm border ${
            toast.kind === 'success'
              ? 'border-green-500/40 bg-green-500/10 text-green-300'
              : 'border-red-500/40 bg-red-500/10 text-red-300'
          }`}
        >
          {toast.msg}
        </div>
      )}

      {/* Filters */}
      <div className="glass rounded-2xl p-4 flex flex-wrap items-center gap-3">
        <input
          type="text"
          placeholder="Search email..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="flex-1 min-w-[220px] h-9 px-3 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm text-white placeholder:text-[var(--fg-tertiary)] focus:outline-none focus:border-[var(--brand-400)] transition-colors"
        />
        <Select
          value={tierFilter}
          onChange={(v) => { setTierFilter(v); setPage(1); }}
          options={[
            { value: '', label: 'All tiers' },
            { value: 'free', label: 'Free' },
            { value: 'pro', label: 'Pro' },
            { value: 'enterprise', label: 'Enterprise' },
          ]}
        />
        <Select
          value={statusFilter}
          onChange={(v) => { setStatusFilter(v); setPage(1); }}
          options={[
            { value: '', label: 'All status' },
            { value: 'active', label: 'Active' },
            { value: 'banned', label: 'Banned' },
            { value: 'deleted', label: 'Deleted' },
          ]}
        />
        <Select
          value={roleFilter}
          onChange={(v) => { setRoleFilter(v); setPage(1); }}
          options={[
            { value: '', label: 'All roles' },
            { value: 'user', label: 'User' },
            { value: 'admin', label: 'Admin' },
            { value: 'super_admin', label: 'Super admin' },
          ]}
        />
      </div>

      {/* Table */}
      <div className="glass rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[var(--surface)] border-b border-[var(--glass-border)]">
            <tr>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Email</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Name</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Tier</th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Credits</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Role</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Status</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)] font-semibold">Joined</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="px-4 py-12 text-center text-[var(--fg-tertiary)]">Loading…</td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan={7} className="px-4 py-12 text-center text-[var(--fg-tertiary)]">No users</td></tr>
            ) : users.map((u) => (
              <tr key={u.id} className="border-b border-[var(--glass-border)] hover:bg-[var(--surface-hover)]">
                <td className="px-4 py-3">
                  <Link href={`/admin/users/${u.id}`} className="text-[var(--brand-300)] hover:text-[var(--brand-400)]">
                    {u.email}
                  </Link>
                </td>
                <td className="px-4 py-3 text-[var(--fg-secondary)]">{u.full_name || '—'}</td>
                <td className="px-4 py-3 capitalize text-[var(--fg-secondary)]">{u.tier}</td>
                <td className="px-4 py-3 text-right tabular-nums">{u.credits}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-0.5 rounded-md text-xs font-semibold bg-[var(--brand-500)]/20 text-[var(--brand-300)]">
                    {u.role}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {u.deleted_at ? (
                    <span className="text-red-400 text-xs">deleted</span>
                  ) : u.banned_at ? (
                    <span className="text-orange-400 text-xs">banned</span>
                  ) : (
                    <span className="text-green-400 text-xs">active</span>
                  )}
                </td>
                <td className="px-4 py-3 text-xs text-[var(--fg-tertiary)]">
                  {new Date(u.created_at).toLocaleDateString('vi-VN')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <button
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
            className="h-9 px-4 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm text-white disabled:opacity-30"
          >
            ← Previous
          </button>
          <span className="text-sm text-[var(--fg-tertiary)]">
            Page {page} / {totalPages}
          </span>
          <button
            disabled={page === totalPages}
            onClick={() => setPage(page + 1)}
            className="h-9 px-4 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm text-white disabled:opacity-30"
          >
            Next →
          </button>
        </div>
      )}

      <CreateUserModal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onCreated={(user) => {
          showToast('success', `Created ${user.email}`);
          refresh();
          router.push(`/admin/users/${user.id}`);
        }}
      />
    </div>
  );
}
