'use client';

import { BackupManager } from '@/components/admin/backup-manager';

export default function AdminBackupPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">💾 Backup & Restore</h1>
      <div className="glass-strong rounded-2xl p-6">
        <BackupManager />
      </div>
    </div>
  );
}
