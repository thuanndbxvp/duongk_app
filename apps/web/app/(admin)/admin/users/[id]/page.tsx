'use client';

import { useMemo, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useArrayFetch, useObjectFetch } from '@/lib/use-fetch';
import { Select } from '@/components/select';
import { ConfirmDialog } from '@/components/confirm-dialog';

interface UserDetail {
  id: string;
  email: string;
  full_name: string | null;
  credits: number;
  tier: string;
  role: string;
  banned_at: string | null;
  banned_reason: string | null;
  deleted_at: string | null;
  max_assistants: number;
  created_at: string;
  last_sign_in_at: string | null;
  counts?: { jobs: number; assistants: number; scripts: number };
}

interface Job {
  id: string;
  type: string;
  status: string;
  created_at: string;
}

interface Transaction {
  id: string;
  action: string;
  amount: number;
  balance_after: number;
  reason: string;
  created_at: string;
}

interface AuditLog {
  id: string;
  admin_email: string;
  action: string;
  target_type: string;
  target_id: string;
  created_at: string;
}

type Tab = 'profile' | 'credits' | 'jobs' | 'audit';

const QUICK_PRESETS = [
  { label: '−100', value: -100 },
  { label: '+100', value: 100 },
  { label: '+500', value: 500 },
  { label: '+1000', value: 1000 },
];

const CLAMP = { min: -10_000, max: 10_000 };
const CONFIRM_THRESHOLD = 1000; // |delta| ≥ 1000 → require explicit confirmation

function formatInt(n: number) {
  return n.toLocaleString('vi-VN');
}

export default function UserDetailPage() {
  const params = useParams();
  const router = useRouter();
  const userId = params.id as string;

  const { data: fetchedUser, refresh } = useObjectFetch<UserDetail>(
    userId ? `/api/admin/users/${userId}` : null,
    [userId],
  );

  const [tab, setTab] = useState<Tab>('profile');
  const [toast, setToast] = useState<{ kind: 'success' | 'error'; msg: string } | null>(null);
  const showToast = (kind: 'success' | 'error', msg: string) => {
    setToast({ kind, msg });
    window.setTimeout(() => setToast(null), 3500);
  };

  // --- Edit Profile state ---
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState<{
    full_name: string;
    tier: string;
    role: string;
    max_assistants: number;
  } | null>(null);
  const startEdit = () => {
    if (!fetchedUser) return;
    setEditForm({
      full_name: fetchedUser.full_name ?? '',
      tier: fetchedUser.tier,
      role: fetchedUser.role,
      max_assistants: fetchedUser.max_assistants,
    });
    setEditing(true);
  };

  // --- Adjust Credit state ---
  const [delta, setDelta] = useState(0);
  const [reason, setReason] = useState('');
  const [adjusting, setAdjusting] = useState(false);

  // --- Destructive actions state ---
  const [confirm, setConfirm] = useState<null | {
    title: string;
    description: React.ReactNode;
    confirmLabel: string;
    danger?: boolean;
    requireText?: string;
    busy?: boolean;
    action: () => Promise<void>;
  }>(null);

  // --- Per-tab fetches ---
  const { data: jobs } = useArrayFetch<Job>(
    tab === 'jobs' ? `/api/jobs/recent?user_id=${userId}&limit=50` : null,
    [tab, userId],
    'jobs',
  );

  const { data: txs } = useArrayFetch<Transaction>(
    tab === 'credits' ? `/api/admin/credit/ledger?user_id=${userId}&limit=100` : null,
    [tab, userId],
    'transactions',
  );

  const { data: auditLogs } = useArrayFetch<AuditLog>(
    tab === 'audit' ? `/api/admin/audit-logs?target_id=${userId}&limit=100` : null,
    [tab, userId],
    'logs',
  );

  // --- Adjust Credit derived ---
  const previewBalance = useMemo(() => {
    if (!fetchedUser) return null;
    return fetchedUser.credits + delta;
  }, [fetchedUser, delta]);

  const reasonTrimmed = reason.trim();
  const reasonValid = reasonTrimmed.length >= 10;
  const deltaValid = Number.isInteger(delta) && delta >= CLAMP.min && delta <= CLAMP.max && delta !== 0;
  const adjustPreviewSummary = useMemo(() => {
    if (!fetchedUser) return null;
    if (!reasonValid || !deltaValid) return null;
    const after = fetchedUser.credits + delta;
    const sign = delta > 0 ? '+' : '';
    const tone = delta > 0 ? 'text-green-400' : 'text-red-400';
    return {
      text: `${formatInt(fetchedUser.credits)} → ${formatInt(after)} (${sign}${formatInt(delta)})`,
      tone,
      after,
    };
  }, [fetchedUser, reasonValid, deltaValid, delta]);

  // --- Action handlers ---

  async function handleSaveEdit() {
    if (!editForm) return;
    setConfirm({
      title: 'Lưu thay đổi',
      description: 'Cập nhật các trường hồ sơ cho người dùng này. Thao tác sẽ được ghi audit log.',
      confirmLabel: 'Lưu',
      busy: true,
      action: async () => {
        const res = await fetch(`/api/admin/users/${userId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(editForm),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          showToast('error', typeof data?.detail === 'string' ? data.detail : `HTTP ${res.status}`);
        } else {
          showToast('success', 'Đã cập nhật người dùng');
          setEditing(false);
          setEditForm(null);
          refresh();
        }
        setConfirm(null);
      },
    });
  }

  async function performAdjust() {
    const res = await fetch(`/api/admin/users/${userId}/adjust-credit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ delta, reason: reasonTrimmed }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      showToast('error', typeof data?.detail === 'string' ? data.detail : `HTTP ${res.status}`);
    } else {
      const nb = typeof data?.new_balance === 'number' ? data.new_balance : null;
      showToast('success', nb !== null ? `Số dư mới: ${formatInt(nb)}` : 'Đã điều chỉnh credit');
      setDelta(0);
      setReason('');
      refresh();
    }
  }

  function handleAdjust() {
    if (!fetchedUser) return;
    if (!deltaValid) {
      showToast('error', `Delta phải là số nguyên từ ${CLAMP.min} đến ${CLAMP.max} và khác 0`);
      return;
    }
    if (!reasonValid) {
      showToast('error', 'Lý do phải có ít nhất 10 ký tự');
      return;
    }

    const after = fetchedUser.credits + delta;
    const sign = delta > 0 ? '+' : '';
    const tone = delta > 0 ? 'text-green-400' : 'text-red-400';
    const isLarge = Math.abs(delta) >= CONFIRM_THRESHOLD;
    const isDeduct = delta < 0;

    // Small positive delta: skip confirmation (low risk).
    if (!isLarge && !isDeduct) {
      setAdjusting(true);
      performAdjust().finally(() => setAdjusting(false));
      return;
    }

    setConfirm({
      title: 'Xác nhận điều chỉnh credit',
      description: (
        <div className="space-y-2">
          <p>
            User <span className="font-semibold">{fetchedUser.email}</span>:{' '}
            <span className="tabular-nums">{formatInt(fetchedUser.credits)}</span>{' '}
            <span className={tone}>→ {formatInt(after)}</span>{' '}
            <span className={`tabular-nums ${tone}`}>({sign}{formatInt(delta)})</span>
          </p>
          <p className="text-xs text-[var(--fg-tertiary)]">
            Lý do: <span className="text-[var(--fg-secondary)]">{reasonTrimmed}</span>
          </p>
          {isDeduct && (
            <p className="text-xs text-orange-300">
              ⚠ Người dùng sẽ bị trừ credit. Thao tác không thể hoàn tác nếu không có giao dịch bù.
            </p>
          )}
          {isLarge && (
            <p className="text-xs text-orange-300">
              ⚠ Delta lớn (≥ {formatInt(CONFIRM_THRESHOLD)}). Vui lòng xác nhận.
            </p>
          )}
        </div>
      ),
      confirmLabel: delta > 0 ? 'Cấp credit' : 'Trừ credit',
      danger: isDeduct,
      busy: true,
      action: async () => {
        await performAdjust();
        setConfirm(null);
      },
    });
  }

  function handleBan() {
    if (!fetchedUser) return;
    // Capture values into local consts so the inner closure has a non-null type.
    const banEmail = fetchedUser.email;
    const banUserId = userId;
    setConfirm({
      title: 'Cấm người dùng',
      description: `Người dùng sẽ không thể đăng nhập. Lý do (≥ 10 ký tự) là bắt buộc và được ghi audit log.`,
      confirmLabel: 'Cấm',
      danger: true,
      requireText: banEmail,
      action: async () => {
        const reasonText = (document.activeElement as HTMLInputElement | null)?.value ?? '';
        const res = await fetch(`/api/admin/users/${banUserId}/ban`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reason: `Banned: ${reasonText || banEmail}` }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          showToast('error', typeof data?.detail === 'string' ? data.detail : `HTTP ${res.status}`);
        } else {
          showToast('success', 'Đã cấm người dùng');
          refresh();
        }
        setConfirm(null);
      },
    });
  }

  async function handleUnban() {
    const res = await fetch(`/api/admin/users/${userId}/unban`, { method: 'POST' });
    if (res.ok) {
      showToast('success', 'Đã bỏ cấm người dùng');
      refresh();
    } else {
      showToast('error', `HTTP ${res.status}`);
    }
  }

  function handleDelete() {
    if (!fetchedUser) return;
    const deleteEmail = fetchedUser.email;
    const deleteUserId = userId;
    setConfirm({
      title: 'Xoá mềm người dùng',
      description: `Người dùng sẽ bị đánh dấu đã xoá và ẩn khỏi danh sách active. Có thể khôi phục trong vòng 7 ngày.`,
      confirmLabel: 'Xoá',
      danger: true,
      requireText: deleteEmail,
      action: async () => {
        const res = await fetch(`/api/admin/users/${deleteUserId}`, {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reason: `Soft-deleted via admin panel` }),
        });
        if (!res.ok && res.status !== 204) {
          const data = await res.json().catch(() => ({}));
          showToast('error', typeof data?.detail === 'string' ? data.detail : `HTTP ${res.status}`);
        } else {
          showToast('success', 'Đã xoá mềm người dùng');
          refresh();
        }
        setConfirm(null);
      },
    });
  }

  async function handleRestore() {
    const res = await fetch(`/api/admin/users/${userId}/restore`, { method: 'POST' });
    if (res.ok) {
      showToast('success', 'Đã khôi phục người dùng');
      refresh();
    } else {
      showToast('error', `HTTP ${res.status}`);
    }
  }

  function handleImpersonate() {
    if (!fetchedUser) return;
    const impersonateEmail = fetchedUser.email;
    const impersonateUserId = userId;
    setConfirm({
      title: 'Mạo danh người dùng',
      description: `Một session token ngắn hạn (15 phút) sẽ được cấp. Mọi thao tác của bạn khi mạo danh đều được ghi audit log cùng admin ID.`,
      confirmLabel: 'Mạo danh',
      danger: true,
      requireText: impersonateEmail,
      action: async () => {
        const res = await fetch(`/api/admin/users/${impersonateUserId}/impersonate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ttl_minutes: 15 }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          showToast('error', typeof data?.detail === 'string' ? data.detail : `HTTP ${res.status}`);
        } else {
          showToast('success', `Đã cấp impersonation token (TTL ${data.expires_in ?? '?'}s). Xem console.`);
          // eslint-disable-next-line no-console
          console.info('[impersonate]', data);
        }
        setConfirm(null);
      },
    });
  }

  if (!fetchedUser) {
    return <div className="p-8 text-center text-[var(--fg-tertiary)]">Đang tải…</div>;
  }

  // TS narrowing: after the guard above, `fetchedUser` is non-null.
  // Bind a local alias so nested closures (setConfirm callbacks) see UserDetail.
  const user = fetchedUser;

  const isDeleted = !!user.deleted_at;
  const isBanned = !!user.banned_at;

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <button
        onClick={() => router.back()}
        className="text-[var(--brand-300)] hover:text-[var(--brand-400)] text-sm"
      >
        ← Quay lại danh sách
      </button>

      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold">{user.email}</h1>
          <p className="text-sm text-[var(--fg-tertiary)]">
            {user.role} · {user.tier} · Tham gia {new Date(user.created_at).toLocaleDateString('vi-VN')}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {!isDeleted && (
            <button
              onClick={startEdit}
              className="h-9 px-3 rounded-lg bg-[var(--brand-500)] text-white text-sm font-semibold hover:bg-[var(--brand-400)]"
            >
              Sửa hồ sơ
            </button>
          )}
          {isDeleted ? (
            <button
              onClick={handleRestore}
              className="h-9 px-3 rounded-lg bg-green-500/20 text-green-300 text-sm font-semibold hover:bg-green-500/30"
            >
              Khôi phục
            </button>
          ) : (
            <>
              {isBanned ? (
                <button
                  onClick={handleUnban}
                  className="h-9 px-3 rounded-lg bg-green-500/20 text-green-300 text-sm font-semibold hover:bg-green-500/30"
                >
                  Bỏ cấm
                </button>
              ) : (
                <button
                  onClick={handleBan}
                  className="h-9 px-3 rounded-lg bg-orange-500/20 text-orange-300 text-sm font-semibold hover:bg-orange-500/30"
                >
                  Cấm
                </button>
              )}
              <button
                onClick={handleImpersonate}
                className="h-9 px-3 rounded-lg bg-purple-500/20 text-purple-300 text-sm font-semibold hover:bg-purple-500/30"
              >
                Mạo danh
              </button>
              <button
                onClick={handleDelete}
                className="h-9 px-3 rounded-lg bg-red-500/20 text-red-300 text-sm font-semibold hover:bg-red-500/30"
              >
                Xoá
              </button>
            </>
          )}
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

      {isDeleted && (
        <div className="rounded-xl px-4 py-3 text-sm border border-red-500/40 bg-red-500/10 text-red-300">
          Người dùng đã bị xoá mềm (xoá lúc {new Date(user.deleted_at!).toLocaleString('vi-VN')}). Khôi phục trong vòng 7 ngày.
        </div>
      )}
      {isBanned && !isDeleted && (
        <div className="rounded-xl px-4 py-3 text-sm border border-orange-500/40 bg-orange-500/10 text-orange-300">
          Đã bị cấm{user.banned_reason ? `: ${user.banned_reason}` : ''}.
        </div>
      )}

      <div className="grid md:grid-cols-3 gap-4">
        {/* Profile */}
        <div className="glass rounded-2xl p-5 space-y-3">
          <h2 className="text-lg font-semibold">Hồ sơ</h2>
          <div className="space-y-2 text-sm">
            <div><span className="text-[var(--fg-tertiary)]">Email:</span> {user.email}</div>
            <div><span className="text-[var(--fg-tertiary)]">Tên:</span> {user.full_name || '—'}</div>
            <div><span className="text-[var(--fg-tertiary)]">Gói:</span> <span className="capitalize">{user.tier}</span></div>
            <div><span className="text-[var(--fg-tertiary)]">Vai trò:</span> {user.role}</div>
            <div><span className="text-[var(--fg-tertiary)]">Max assistants:</span> {user.max_assistants}</div>
            <div><span className="text-[var(--fg-tertiary)]">Đăng nhập gần nhất:</span> {user.last_sign_in_at ? new Date(user.last_sign_in_at).toLocaleString('vi-VN') : '—'}</div>
          </div>
        </div>

        {/* Stats */}
        <div className="glass rounded-2xl p-5 space-y-3">
          <h2 className="text-lg font-semibold">Thống kê</h2>
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-[var(--fg-tertiary)]">Số dư credit:</span>{' '}
              <span className="text-2xl font-bold tabular-nums">{formatInt(user.credits)}</span>
            </div>
            <div><span className="text-[var(--fg-tertiary)]">Jobs:</span> {user.counts?.jobs ?? 0}</div>
            <div><span className="text-[var(--fg-tertiary)]">Assistants:</span> {user.counts?.assistants ?? 0}</div>
            <div><span className="text-[var(--fg-tertiary)]">Scripts:</span> {user.counts?.scripts ?? 0}</div>
          </div>
        </div>

        {/* Adjust credit */}
        <div className="glass rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Điều chỉnh credit</h2>
            <span className="text-xs text-[var(--fg-tertiary)]" title="Có thể cấp (+) hoặc trừ (−) credit">
              Cấp / Trừ thủ công
            </span>
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-[var(--fg-tertiary)] mb-1">
              Số lượng (delta)
            </label>
            <input
              type="number"
              value={delta}
              min={CLAMP.min}
              max={CLAMP.max}
              step={1}
              onChange={(e) => setDelta(Number(e.target.value))}
              placeholder={`${CLAMP.min} đến ${CLAMP.max}`}
              className="w-full h-9 px-3 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm text-white focus:outline-none focus:border-[var(--brand-400)]"
            />
          </div>

          <div className="flex flex-wrap gap-1.5">
            {QUICK_PRESETS.map((p) => (
              <button
                key={p.label}
                type="button"
                onClick={() => setDelta(p.value)}
                className={`h-7 px-2.5 rounded-md text-xs font-semibold border transition-colors ${
                  p.value > 0
                    ? 'bg-green-500/10 border-green-500/30 text-green-300 hover:bg-green-500/20'
                    : 'bg-red-500/10 border-red-500/30 text-red-300 hover:bg-red-500/20'
                }`}
                title={`Đặt delta = ${p.value}`}
              >
                {p.label}
              </button>
            ))}
            <button
              type="button"
              onClick={() => setDelta(0)}
              className="h-7 px-2.5 rounded-md text-xs font-semibold border bg-[var(--surface)] border-[var(--glass-border)] text-[var(--fg-tertiary)] hover:text-[var(--fg-primary)]"
              title="Đặt lại về 0"
            >
              Reset
            </button>
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-[var(--fg-tertiary)] mb-1">
              Lý do <span className="text-red-400">*</span>{' '}
              <span className="text-[var(--fg-tertiary)] normal-case">({reasonTrimmed.length}/10+)</span>
            </label>
            <input
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="VD: Bù credit do lỗi job #abc, refund support ticket #42"
              className="w-full h-9 px-3 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm text-white placeholder:text-[var(--fg-tertiary)] focus:outline-none focus:border-[var(--brand-400)]"
            />
          </div>

          {adjustPreviewSummary && (
            <div
              className={`rounded-lg px-3 py-2 text-xs border ${
                delta > 0
                  ? 'border-green-500/30 bg-green-500/5 text-green-300'
                  : 'border-red-500/30 bg-red-500/5 text-red-300'
              }`}
              title="Số dư ước tính sau khi điều chỉnh"
            >
              Preview: <span className="tabular-nums">{adjustPreviewSummary.text}</span>
            </div>
          )}

          {previewBalance !== null && previewBalance < 0 && (
            <p className="text-xs text-orange-300">
              ⚠ Số dư sau khi trừ sẽ âm ({formatInt(previewBalance)}). Vẫn cho phép nếu bạn xác nhận.
            </p>
          )}

          <button
            onClick={handleAdjust}
            disabled={adjusting || !deltaValid || !reasonValid}
            className="w-full h-9 rounded-lg bg-[var(--brand-500)] text-white text-sm font-semibold hover:bg-[var(--brand-400)] disabled:opacity-50 disabled:cursor-not-allowed"
            title={
              !deltaValid
                ? 'Delta phải là số nguyên khác 0 trong khoảng cho phép'
                : !reasonValid
                  ? 'Lý do phải có ít nhất 10 ký tự'
                  : 'Gửi yêu cầu điều chỉnh'
            }
          >
            {adjusting ? 'Đang điều chỉnh…' : `Điều chỉnh (${delta > 0 ? 'Cấp' : delta < 0 ? 'Trừ' : '—'})`}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="glass rounded-2xl overflow-hidden">
        <div className="flex border-b border-[var(--glass-border)]">
          {([
            ['profile', 'Hồ sơ'],
            ['credits', 'Lịch sử credit'],
            ['jobs', 'Jobs'],
            ['audit', 'Audit log'],
          ] as Array<[Tab, string]>).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`px-4 py-3 text-sm font-medium transition ${
                tab === key
                  ? 'text-white border-b-2 border-[var(--brand-400)]'
                  : 'text-[var(--fg-tertiary)] hover:text-white'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="p-5">
          {tab === 'profile' && editing && editForm && (
            <div className="space-y-3 max-w-md">
              <Field label="Họ tên">
                <input
                  type="text"
                  value={editForm.full_name}
                  onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                  className="w-full h-9 px-3 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm text-white focus:outline-none focus:border-[var(--brand-400)]"
                />
              </Field>
              <Field label="Gói">
                <Select
                  value={editForm.tier}
                  onChange={(v) => setEditForm({ ...editForm, tier: v })}
                  options={[
                    { value: 'free', label: 'Free' },
                    { value: 'pro', label: 'Pro' },
                    { value: 'enterprise', label: 'Enterprise' },
                  ]}
                />
              </Field>
              <Field label="Vai trò">
                <Select
                  value={editForm.role}
                  onChange={(v) => setEditForm({ ...editForm, role: v })}
                  options={[
                    { value: 'user', label: 'User' },
                    { value: 'admin', label: 'Admin' },
                    { value: 'super_admin', label: 'Super admin' },
                  ]}
                />
              </Field>
              <Field label="Max assistants">
                <input
                  type="number"
                  min={0}
                  max={1000}
                  value={editForm.max_assistants}
                  onChange={(e) => setEditForm({ ...editForm, max_assistants: Number(e.target.value) })}
                  className="w-full h-9 px-3 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm text-white focus:outline-none focus:border-[var(--brand-400)]"
                />
              </Field>
              <div className="flex gap-2">
                <button
                  onClick={() => { setEditing(false); setEditForm(null); }}
                  className="h-9 px-3 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-sm text-[var(--fg-secondary)]"
                >
                  Huỷ
                </button>
                <button
                  onClick={handleSaveEdit}
                  className="h-9 px-3 rounded-lg bg-[var(--brand-500)] text-white text-sm font-semibold hover:bg-[var(--brand-400)]"
                >
                  Lưu
                </button>
              </div>
            </div>
          )}

          {tab === 'profile' && !editing && (
            <p className="text-sm text-[var(--fg-tertiary)]">
              Bấm <span className="text-white font-semibold">Sửa hồ sơ</span> để thay đổi tên, gói, vai trò, hoặc max assistants.
            </p>
          )}

          {tab === 'credits' && (
            <TxTable txs={txs} />
          )}

          {tab === 'jobs' && (
            <div>
              <p className="text-sm text-[var(--fg-tertiary)]">
                Lịch sử jobs cần endpoint riêng (xem <code>PLAN-phase6-admin-user-credit.md</code>). Chưa implement — backend <code>/api/jobs/recent/list</code> trả về jobs của admin, không phải user này.
              </p>
              {jobs.length > 0 && (
                <div className="mt-3 overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="border-b border-[var(--glass-border)]">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs uppercase text-[var(--fg-tertiary)]">Loại</th>
                        <th className="px-3 py-2 text-left text-xs uppercase text-[var(--fg-tertiary)]">Trạng thái</th>
                        <th className="px-3 py-2 text-left text-xs uppercase text-[var(--fg-tertiary)]">Tạo lúc</th>
                      </tr>
                    </thead>
                    <tbody>
                      {jobs.map((j) => (
                        <tr key={j.id} className="border-b border-[var(--glass-border)]">
                          <td className="px-3 py-2">{j.type}</td>
                          <td className="px-3 py-2">{j.status}</td>
                          <td className="px-3 py-2 text-xs text-[var(--fg-tertiary)]">{new Date(j.created_at).toLocaleString('vi-VN')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <p className="text-xs text-[var(--fg-tertiary)] mt-2">
                    (Các hàng trên là jobs của admin — hiển thị tạm.)
                  </p>
                </div>
              )}
            </div>
          )}

          {tab === 'audit' && (
            <AuditTable logs={auditLogs} />
          )}
        </div>
      </div>

      <ConfirmDialog
        open={!!confirm}
        title={confirm?.title ?? ''}
        description={confirm?.description}
        confirmLabel={confirm?.confirmLabel}
        danger={confirm?.danger}
        requireText={confirm?.requireText}
        busy={confirm?.busy}
        onConfirm={async () => { await confirm?.action(); }}
        onCancel={() => setConfirm(null)}
      />
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-1.5">
      <span className="text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">{label}</span>
      {children}
    </label>
  );
}

function TxTable({ txs }: { txs: Transaction[] }) {
  if (txs.length === 0) {
    return <p className="text-sm text-[var(--fg-tertiary)]">Chưa có giao dịch credit nào.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-[var(--glass-border)]">
          <tr>
            <th className="px-3 py-2 text-left text-xs uppercase text-[var(--fg-tertiary)]">Hành động</th>
            <th className="px-3 py-2 text-right text-xs uppercase text-[var(--fg-tertiary)]">Số lượng</th>
            <th className="px-3 py-2 text-right text-xs uppercase text-[var(--fg-tertiary)]">Số dư</th>
            <th className="px-3 py-2 text-left text-xs uppercase text-[var(--fg-tertiary)]">Lý do</th>
            <th className="px-3 py-2 text-left text-xs uppercase text-[var(--fg-tertiary)]">Thời gian</th>
          </tr>
        </thead>
        <tbody>
          {txs.map((tx) => (
            <tr key={tx.id} className="border-b border-[var(--glass-border)]">
              <td className="px-3 py-2 text-[var(--brand-300)]">{tx.action}</td>
              <td className={`px-3 py-2 text-right tabular-nums ${tx.amount > 0 ? 'text-green-400' : 'text-red-400'}`}>
                {tx.amount > 0 ? '+' : ''}{formatInt(tx.amount)}
              </td>
              <td className="px-3 py-2 text-right tabular-nums">{formatInt(tx.balance_after)}</td>
              <td className="px-3 py-2 text-xs text-[var(--fg-tertiary)] max-w-xs truncate" title={tx.reason || ''}>{tx.reason || '—'}</td>
              <td className="px-3 py-2 text-xs text-[var(--fg-tertiary)]">{new Date(tx.created_at).toLocaleString('vi-VN')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function JobsTable({ jobs }: { jobs: Job[] }) {
  if (jobs.length === 0) {
    return <p className="text-sm text-[var(--fg-tertiary)]">Chưa có job gần đây.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-[var(--glass-border)]">
          <tr>
            <th className="px-3 py-2 text-left text-xs uppercase text-[var(--fg-tertiary)]">Loại</th>
            <th className="px-3 py-2 text-left text-xs uppercase text-[var(--fg-tertiary)]">Trạng thái</th>
            <th className="px-3 py-2 text-left text-xs uppercase text-[var(--fg-tertiary)]">Tạo lúc</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((j) => (
            <tr key={j.id} className="border-b border-[var(--glass-border)]">
              <td className="px-3 py-2">{j.type}</td>
              <td className="px-3 py-2">
                <span className="px-2 py-0.5 rounded-md text-xs font-semibold bg-[var(--brand-500)]/20 text-[var(--brand-300)]">
                  {j.status}
                </span>
              </td>
              <td className="px-3 py-2 text-xs text-[var(--fg-tertiary)]">{new Date(j.created_at).toLocaleString('vi-VN')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AuditTable({ logs }: { logs: AuditLog[] }) {
  if (logs.length === 0) {
    return <p className="text-sm text-[var(--fg-tertiary)]">Chưa có audit log cho người dùng này.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-[var(--glass-border)]">
          <tr>
            <th className="px-3 py-2 text-left text-xs uppercase text-[var(--fg-tertiary)]">Thời gian</th>
            <th className="px-3 py-2 text-left text-xs uppercase text-[var(--fg-tertiary)]">Admin</th>
            <th className="px-3 py-2 text-left text-xs uppercase text-[var(--fg-tertiary)]">Hành động</th>
            <th className="px-3 py-2 text-left text-xs uppercase text-[var(--fg-tertiary)]">Đối tượng</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.id} className="border-b border-[var(--glass-border)]">
              <td className="px-3 py-2 text-xs text-[var(--fg-tertiary)]">{new Date(log.created_at).toLocaleString('vi-VN')}</td>
              <td className="px-3 py-2 text-[var(--fg-secondary)]">{log.admin_email}</td>
              <td className="px-3 py-2 text-[var(--brand-300)]">{log.action}</td>
              <td className="px-3 py-2 text-xs text-[var(--fg-tertiary)]">{log.target_type}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
