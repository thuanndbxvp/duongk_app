import { TopBar } from '@/components/layout/topbar';
import { AuthenticatedLayout } from '@/components/layout/authenticated-layout';

export default function DashboardGroupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex flex-col">
      <TopBar />
      <AuthenticatedLayout>{children}</AuthenticatedLayout>
    </div>
  );
}
