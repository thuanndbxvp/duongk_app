import { redirect } from 'next/navigation';
import { apiFetch } from '../../../../lib/api-client';
import { getAccessToken } from '../../../../lib/auth';
import { ProfileForm } from '../../../../components/profile-form';
import { PasswordForm } from '../../../../components/password-form';

export default async function AccountSettingsPage() {
  const token = await getAccessToken();
  if (!token) redirect('/login');

  const res = await apiFetch('/api/users/me', {}, token);
  if (!res.ok) redirect('/login');

  const user = await res.json();

  return (
    <main className="container mx-auto p-8 max-w-2xl">
      <h1 className="text-3xl font-bold mb-8">Account Settings</h1>

      <div className="space-y-6">
        {/* Profile */}
        <section className="bg-white rounded-lg shadow border p-6">
          <h2 className="text-xl font-bold mb-4">Profile</h2>
          <ProfileForm
            initial={{
              email: user.email,
              full_name: user.full_name,
              avatar_url: user.avatar_url,
            }}
          />
        </section>

        {/* Security */}
        <section className="bg-white rounded-lg shadow border p-6">
          <h2 className="text-xl font-bold mb-4">Security</h2>
          <PasswordForm />
        </section>

        {/* Danger Zone */}
        <section className="bg-white rounded-lg shadow border border-red-300 p-6">
          <h2 className="text-xl font-bold mb-2 text-red-600">Danger Zone</h2>
          <p className="text-sm text-gray-600 mb-4">
            Xóa tài khoản sẽ xóa tất cả dữ liệu vĩnh viễn. Hành động này không thể hoàn tác.
          </p>
          <button
            onClick={() => {
              if (confirm('Bạn chắc chắn muốn xóa tài khoản?')) {
                alert('Liên hệ support@appdk.vn để xóa tài khoản.');
              }
            }}
            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Xóa tài khoản
          </button>
        </section>
      </div>
    </main>
  );
}
