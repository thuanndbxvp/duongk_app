import Link from 'next/link';
import { CreditsBadge } from '@/components/credits-badge';
import { UserMenu } from './user-menu';
import { MobileMenu } from './mobile-menu';
import { getFullUser, type FullUser } from '@/lib/auth';
import { IconSparkle } from '@/components/icons';

async function getCurrentUser(): Promise<FullUser | null> {
  return await getFullUser();
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
                className="bg-[#3b82f6] hover:bg-[#2563eb] transition-colors h-10 px-6 rounded-lg text-sm font-semibold text-white flex items-center justify-center shadow-md"
              >
                Login
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
