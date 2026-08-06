import { redirect } from 'next/navigation';
import { getAccessToken, getFullUser } from '@/lib/auth';
import { Sidebar } from './sidebar';
import { Breadcrumbs } from './breadcrumbs';

export async function AuthenticatedLayout({
  children,
  showBreadcrumbs = true,
}: {
  children: React.ReactNode;
  showBreadcrumbs?: boolean;
}) {
  const token = await getAccessToken();
  if (!token) redirect('/login');

  const user = await getFullUser();
  const userRole = user?.role ?? 'user';

  const breadcrumbs: { label: string; href: string }[] = [];

  return (
    <div className="flex flex-1">
      <aside className="hidden lg:block w-64 shrink-0 sticky top-[68px] h-[calc(100dvh-68px)]">
        <div className="h-full glass border-r border-[var(--glass-border)]">
          <Sidebar userRole={userRole} />
        </div>
      </aside>

      <main className="flex-1 min-w-0 px-4 lg:px-10 py-6 lg:py-10">
        {showBreadcrumbs && breadcrumbs.length > 0 && (
          <Breadcrumbs items={breadcrumbs} />
        )}
        {children}
      </main>
    </div>
  );
}
