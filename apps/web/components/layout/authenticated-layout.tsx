import { redirect } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
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

  // For now, breadcrumbs are computed client-side or omitted if empty
  const breadcrumbs: { label: string; href: string }[] = [];

  return (
    <div className="flex flex-1">
      <aside className="hidden lg:block w-64 border-r bg-white sticky top-16 h-[calc(100vh-4rem)]">
        <Sidebar />
      </aside>

      <main className="flex-1 p-4 lg:p-8 overflow-x-hidden">
        {showBreadcrumbs && breadcrumbs.length > 0 && (
          <Breadcrumbs items={breadcrumbs} />
        )}
        {children}
      </main>
    </div>
  );
}
