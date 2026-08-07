'use client';

export function UserTable({ users }: { users: { id: string; email: string; tier: string; created_at: string }[] }) {
  if (!users || users.length === 0) return <p className="text-xs text-[var(--fg-tertiary)]">No users found.</p>;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[var(--glass-border)] text-left">
            <th className="py-2 px-3 text-xs text-[var(--fg-tertiary)]">Email</th>
            <th className="py-2 px-3 text-xs text-[var(--fg-tertiary)]">Tier</th>
            <th className="py-2 px-3 text-xs text-[var(--fg-tertiary)]">Created</th>
          </tr>
        </thead>
        <tbody>
          {users.map(u => (
            <tr key={u.id} className="border-b border-[var(--glass-border)]/50 hover:bg-white/[0.02]">
              <td className="py-2 px-3 text-[var(--fg-secondary)]">{u.email}</td>
              <td className="py-2 px-3">
                <span className={`text-xs px-2 py-0.5 rounded ${u.tier === 'admin' ? 'bg-purple-500/20 text-purple-400' : 'bg-blue-500/20 text-blue-400'}`}>{u.tier || 'user'}</span>
              </td>
              <td className="py-2 px-3 text-xs text-[var(--fg-tertiary)]">{u.created_at ? new Date(u.created_at).toLocaleDateString('vi-VN') : '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
