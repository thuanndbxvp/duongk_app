import Link from 'next/link';
import { CreditsBadge } from '@/components/credits-badge';
import { UserMenu } from './user-menu';
import { MobileMenu } from './mobile-menu';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

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
    <header className="sticky top-0 z-40 bg-white border-b">
      <div className="px-4 lg:px-8 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <MobileMenu />
          <Link href="/" className="font-bold text-xl text-blue-600">
            AppDK
          </Link>
        </div>

        <div className="flex items-center gap-3">
          {user && <CreditsBadge />}
          {user ? (
            <UserMenu user={user} />
          ) : (
            <Link
              href="/login"
              className="bg-blue-600 text-white px-4 py-2 rounded text-sm"
            >
              Login
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
