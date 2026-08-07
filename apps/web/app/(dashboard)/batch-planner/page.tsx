'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function BatchPlannerPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to dashboard for now - batch planner is a future feature
    router.replace('/dashboard');
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <div className="text-center">
        <div className="animate-spin w-8 h-8 border-2 border-[var(--brand-300)] border-t-transparent rounded-full mx-auto" />
        <p className="mt-4 text-[var(--fg-secondary)]">Loading Batch Planner...</p>
      </div>
    </div>
  );
}
