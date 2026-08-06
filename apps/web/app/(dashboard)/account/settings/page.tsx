import { redirect } from 'next/navigation';
import { getAccessToken, getFullUser } from '@/lib/auth';
import { ProfileForm } from '@/components/profile-form';
import { PasswordForm } from '@/components/password-form';
import { IconUser, IconShield } from '@/components/icons';

const isDevMode = process.env.NEXT_PUBLIC_SUPABASE_URL?.includes('xxx');

async function getUserData() {
  const token = await getAccessToken();
  if (!token) redirect('/login');

  // In dev mode, decode user directly from the mock JWT (no backend roundtrip)
  if (isDevMode) {
    const user = await getFullUser();
    if (!user) redirect('/login');
    return {
      email: user.email,
      full_name: user.full_name,
      avatar_url: user.avatar_url,
    };
  }

  // Production: call FastAPI backend
  const { apiFetch } = await import('@/lib/api-client');
  const res = await apiFetch('/api/users/me', {}, token);
  if (!res.ok) redirect('/login');
  return res.json();
}

export default async function AccountSettingsPage() {
  const user = await getUserData();

  return (
    <div className="space-y-8 animate-fade-up">
      <div className="space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          <IconUser size={14} /> Tài khoản
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">Cài đặt tài khoản</span>
        </h1>
        <p className="text-[var(--fg-secondary)] max-w-xl">
          Cập nhật thông tin cá nhân và bảo mật cho tài khoản của bạn.
        </p>
      </div>

      <div className="max-w-2xl space-y-6">
        <section className="relative glass-strong rounded-2xl p-7 overflow-hidden">
          <div
            aria-hidden
            className="pointer-events-none absolute -top-20 -right-20 h-48 w-48 rounded-full bg-[var(--brand-500)] opacity-15 blur-3xl"
          />
          <div className="relative">
            <h2 className="text-lg font-semibold text-white mb-1">Hồ sơ</h2>
            <p className="text-sm text-[var(--fg-secondary)] mb-5">
              Thông tin hiển thị trên hồ sơ của bạn.
            </p>
            <ProfileForm
              initial={{
                email: user.email,
                full_name: user.full_name,
                avatar_url: user.avatar_url,
              }}
            />
          </div>
        </section>

        <section className="relative glass-strong rounded-2xl p-7 overflow-hidden">
          <div
            aria-hidden
            className="pointer-events-none absolute -top-20 -right-20 h-48 w-48 rounded-full bg-[var(--brand-500)] opacity-15 blur-3xl"
          />
          <div className="relative">
            <h2 className="text-lg font-semibold text-white mb-1">Bảo mật</h2>
            <p className="text-sm text-[var(--fg-secondary)] mb-5">
              Đổi mật khẩu định kỳ để giữ tài khoản an toàn.
            </p>
            <PasswordForm />
          </div>
        </section>
      </div>
    </div>
  );
}