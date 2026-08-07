'use client';

import { useState } from 'react';

export function BackupManager() {
  const [isDownloading, setIsDownloading] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);
  const [lastBackup, setLastBackup] = useState<string | null>(null);

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      const r = await fetch('/api/admin/backup');
      const data = await r.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `backup-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      setLastBackup(new Date().toISOString());
    } finally { setIsDownloading(false); }
  };

  const handleRestore = async (file: File) => {
    if (!confirm('Restore sẽ ghi đè config hiện tại. Tiếp tục?')) return;
    setIsRestoring(true);
    try {
      const text = await file.text();
      const r = await fetch('/api/admin/backup', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: text });
      if (r.ok) alert('✅ Restore thành công');
      else alert('❌ Lỗi: ' + (await r.text()));
    } finally { setIsRestoring(false); }
  };

  return (
    <div className="space-y-4">
      <button onClick={handleDownload} disabled={isDownloading}
        className="px-4 py-2 rounded-lg gradient-bg text-white text-sm font-medium disabled:opacity-50">
        {isDownloading ? '⏳ Generating...' : '📥 Download Backup'}
      </button>

      <label className="inline-block px-4 py-2 rounded-lg bg-white/[0.06] border border-[var(--glass-border)] text-sm text-[var(--fg-secondary)] cursor-pointer hover:text-white">
        {isRestoring ? '⏳ Restoring...' : '📤 Restore from File'}
        <input type="file" accept=".json" className="hidden"
          onChange={e => e.target.files?.[0] && handleRestore(e.target.files[0])} />
      </label>

      {lastBackup && <p className="text-xs text-[var(--fg-tertiary)]">Last backup: {new Date(lastBackup).toLocaleString('vi-VN')}</p>}
    </div>
  );
}
