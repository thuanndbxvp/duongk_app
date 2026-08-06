import Link from 'next/link';
import { IconShield } from '@/components/icons';

export default function ForbiddenPage() {
  return (
    <div className="min-h-dvh flex flex-col items-center justify-center px-4 text-center">
      <div className="relative w-20 h-20 rounded-2xl gradient-bg flex items-center justify-center mb-6 shadow-2xl">
        <IconShield size={36} className="text-white relative" />
      </div>
      <h1 className="text-4xl font-bold gradient-text">403 — Forbidden</h1>
      <p className="mt-3 text-[var(--fg-secondary)] max-w-md">
        Bạn không có quyền truy cập trang này. Khu vực này chỉ dành cho
        admin hoặc super admin.
      </p>
      <Link
        href="/dashboard"
        className="mt-6 inline-flex items-center gap-2 h-11 px-6 rounded-xl text-sm font-semibold text-white gradient-bg btn-glow"
      >
        Về Dashboard
      </Link>
    </div>
  );
}