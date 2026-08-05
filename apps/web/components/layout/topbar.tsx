import Link from 'next/link';
import { CreditsBadge } from '@/components/credits-badge';
import { UserMenu } from './user-menu';
import { MobileMenu } from './mobile-menu';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { IconSparkle } from '@/components/icons';

interface User {
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  tier: string;
  credits: number;
}

async function getCurrentUser(): Promise<User | null> {
  const token = await getAccessToken();
  if (!token) return null;

  try {
    const res = await apiFetch('/api/users/me', {}, token);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function TopBar() {
  const user = await getCurrentUser();

  return (
    <header className="sticky top-0 z-40">
      <div className="glass-strong border-b border-[var(--glass-border)]">
        <div className="px-4 lg:px-8 h-[68px] flex items-center justify-between">
          <div className="flex items-center gap-4">
            <MobileMenu />
            <Link href="/" className="flex items-center gap-2 group">
              <span className="relative inline-flex h-8 w-8 items-center justify-center rounded-xl gradient-bg btn-glow">
                <IconSparkle size={16} className="text-white relative" />
              </span>
              <span className="font-bold text-lg tracking-tight">
                <span className="gradient-text">AppDK</span>
              </span>
            </Link>
          </div>

          <div className="flex items-center gap-3">
            {user && <CreditsBadge />}
            {user ? (
              <UserMenu user={user} />
            ) : (
              <Link
                href="/login"
                className="btn-glow relative inline-flex items-center px-4 h-10 rounded-xl text-sm font-semibold text-white"
              >
                <span className="relative gradient-bg rounded-[10px] px-4 h-10 inline-flex items-center">
                  Login
                </span>
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
