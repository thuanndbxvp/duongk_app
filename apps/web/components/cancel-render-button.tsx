'use client';

import { useState, useRef } from 'react';
import { ConfirmDialog } from '@/components/confirm-dialog';

interface Props {
  projectId: string;
  jobId: string;
  status: string;
  onCancelled?: () => void;
}

export function CancelRenderButton({ projectId, jobId, status, onCancelled }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<'cancelled' | 'refunded' | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  if (status !== 'running' && status !== 'pending') return null;
  if (result) return <span className="text-xs text-green-400">✅ {result === 'refunded' ? 'Đã hủy + refund credits' : 'Đã hủy'}</span>;

  const handleCancel = async () => {
    setIsLoading(true);
    try {
      const r = await fetch(`/api/jobs/${jobId}/cancel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!r.ok) throw new Error(`Cancel failed: ${r.status}`);

      // Poll for cancellation confirmation (max 30s)
      pollRef.current = setInterval(async () => {
        try {
          const statusRes = await fetch(`/api/jobs/${jobId}`);
          const job = await statusRes.json();
          if (job.status === 'cancelled') {
            clearInterval(pollRef.current);
            setResult('cancelled');
            setIsLoading(false);
            onCancelled?.();
          }
        } catch { /* continue polling */ }
      }, 2000);
      setTimeout(() => {
        if (pollRef.current) clearInterval(pollRef.current);
        if (!result) setIsLoading(false);
      }, 30000);
    } catch (e) {
      setIsLoading(false);
      alert('Không thể hủy render: ' + (e as Error).message);
    }
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        disabled={isLoading}
        className="px-3 py-1.5 rounded-lg bg-red-500/20 border border-red-500/30 text-red-400 text-xs font-medium hover:bg-red-500/30 disabled:opacity-50 transition"
      >
        {isLoading ? 'Đang hủy...' : '⏹ Hủy render'}
      </button>
      <ConfirmDialog
        open={isOpen}
        title="Hủy render?"
        description="Render hiện tại sẽ bị dừng. Credits sẽ được refund."
        confirmLabel="Hủy render"
        danger
        busy={isLoading}
        onConfirm={handleCancel}
        onCancel={() => setIsOpen(false)}
      />
    </>
  );
}
