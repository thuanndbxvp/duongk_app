import Link from 'next/link';
import { redirect } from 'next/navigation';
import { jwtDecode } from 'jwt-decode';
import { cookies } from 'next/headers';
import { IconDashboard, IconUsers, IconChannels, IconShield, IconAlert, IconArrowLeft } from '@/components/icons';

const ADMIN_NAV = [
  { href: '/admin', label: 'Dashboard', icon: IconDashboard, enabled: true },
  { href: '/admin/users', label: 'Users', icon: IconUsers, enabled: true },
  { href: '/admin/credits', label: 'Credits', icon: IconChannels, enabled: true },
  { href: '/admin/pricing', label: 'Pricing', icon: IconShield, enabled: false },
  { href: '/admin/api-keys', label: 'API Keys', icon: IconShield, enabled: true },
  { href: '/admin/routing', label: 'Routing', icon: IconChannels, enabled: true },
  { href: '/admin/alerts', label: 'Alerts', icon: IconAlert, enabled: true },
  { href: '/admin/audit-logs', label: 'Audit Logs', icon: IconShield, enabled: true },
  { href: '/admin/security/mfa', label: 'Security', icon: IconShield, enabled: true },
];

interface SessionPayload {
  sub: string;
  email?: string;
  exp: number;
  role?: string;
  full_name?: string | null;
}

const ACCESS_TOKEN_COOKIE = 'sb-access-token';

async function loadSession(): Promise<{
  userId: string;
  email: string;
  role: string;
} | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get(ACCESS_TOKEN_COOKIE)?.value;
  if (!token) return null;

  let payload: SessionPayload | null = null;

  // Dev mock token format: dev.<base64>.mock
  if (token.startsWith('dev.') && token.endsWith('.mock')) {
    try {
      const b64 = token.split('.')[1];
      payload = JSON.parse(Buffer.from(b64, 'base64').toString());
    } catch {
      payload = null;
    }
  } else {
    // Real Supabase JWT
    try {
      payload = jwtDecode<SessionPayload>(token);
    } catch {
      payload = null;
    }
  }

  if (!payload?.exp || payload.exp * 1000 < Date.now()) return null;

  // For dev mock, role is encoded in the token itself
  if (token.startsWith('dev.')) {
    return {
      userId: payload.sub ?? 'dev-user',
      email: payload.email ?? '',
      role: payload.role ?? 'user',
    };
  }

  // For real Supabase, fetch role from REST (only if not in payload)
  if (payload.role) {
    return {
      userId: payload.sub,
      email: payload.email ?? '',
      role: payload.role,
    };
  }

  try {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_SUPABASE_URL}/rest/v1/users?id=eq.${payload.sub}&select=role,email`,
      {
        headers: {
          apikey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
          Authorization: `Bearer ${token}`,
        },
      }
    );
    if (!res.ok) return null;
    const rows = await res.json();
    const row = rows?.[0];
    if (!row) return null;
    return {
      userId: payload.sub,
      email: row.email ?? payload.email ?? '',
      role: row.role ?? 'user',
    };
  } catch {
    return null;
  }
}

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await loadSession();

  if (!session) {
    redirect('/login?next=/admin');
  }

  if (!['admin', 'super_admin'].includes(session.role)) {
    redirect('/403');
  }

  return (
    <div className="min-h-screen flex bg-[var(--bg)]">
      {/* Sidebar */}
      <aside className="w-60 shrink-0 border-r border-[var(--glass-border)] bg-[var(--surface)] flex flex-col">
        <div className="px-5 py-5 border-b border-[var(--glass-border)]">
          <Link href="/admin" className="text-lg font-bold gradient-text">
            Admin Panel
          </Link>
          <p className="text-xs text-[var(--fg-tertiary)] mt-1">
            {session.email}
          </p>
          <span className="inline-block mt-2 px-2 py-0.5 rounded-md text-xs font-semibold bg-[var(--brand-500)]/20 text-[var(--brand-300)]">
            {session.role}
          </span>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          <Link
            href="/dashboard"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition text-[var(--fg-secondary)] hover:bg-[var(--surface-hover)] hover:text-white border border-transparent hover:border-[var(--glass-border)] mb-2"
          >
            <IconArrowLeft size={16} />
            <span>Quay về Dashboard</span>
          </Link>
          {ADMIN_NAV.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.enabled ? item.href : '#'}
                aria-disabled={!item.enabled}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${
                  item.enabled
                    ? 'text-[var(--fg-secondary)] hover:bg-[var(--surface-hover)] hover:text-white'
                    : 'text-[var(--fg-tertiary)] cursor-not-allowed opacity-50'
                }`}
              >
                <Icon size={16} />
                <span>{item.label}</span>
                {!item.enabled && (
                  <span className="ml-auto text-[10px] uppercase tracking-wider opacity-60">
                    Soon
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
        <div className="px-5 py-4 border-t border-[var(--glass-border)] text-xs text-[var(--fg-tertiary)]">
          v0.1.0 · Phase 5
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}