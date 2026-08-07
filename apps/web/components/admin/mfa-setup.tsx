'use client';

import { useState, useEffect } from 'react';

export function MfaSetup() {
  const [status, setStatus] = useState<'loading' | 'disabled' | 'enabled'>('loading');
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [enrolling, setEnrolling] = useState(false);

  useEffect(() => {
    fetch('/api/admin/mfa')
      .then(r => r.json())
      .then(d => setStatus(d.enabled ? 'enabled' : 'disabled'))
      .catch(() => setStatus('disabled'));
  }, []);

  const handleEnroll = async () => {
    setEnrolling(true);
    try {
      const r = await fetch('/api/admin/mfa', { method: 'POST' });
      const d = await r.json();
      setQrCode(d.qr_code || d.data_url);
      setBackupCodes(d.backup_codes || []);
      setStatus('enabled');
    } catch { alert('Enroll failed'); }
    setEnrolling(false);
  };

  const handleDisable = async () => {
    if (!confirm('Disable MFA? This reduces account security.')) return;
    await fetch('/api/admin/mfa', { method: 'DELETE' });
    setStatus('disabled');
    setQrCode(null);
    setBackupCodes([]);
  };

  if (status === 'loading') return <p className="text-xs text-[var(--fg-secondary)]">Loading...</p>;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <span className={`text-xs px-2 py-1 rounded ${status === 'enabled' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
          {status === 'enabled' ? '✅ Enabled' : '⚠️ Disabled'}
        </span>
        {status === 'disabled' ? (
          <button onClick={handleEnroll} disabled={enrolling}
            className="px-3 py-1 rounded-lg gradient-bg text-white text-xs font-medium disabled:opacity-50">
            {enrolling ? 'Enrolling...' : 'Enable MFA'}
          </button>
        ) : (
          <button onClick={handleDisable}
            className="px-3 py-1 rounded-lg bg-red-500/20 border border-red-500/30 text-red-400 text-xs">Disable MFA</button>
        )}
      </div>

      {qrCode && (
        <div className="glass-strong rounded-xl p-4 space-y-3">
          <p className="text-xs font-medium">Scan QR Code</p>
          <img src={qrCode} alt="MFA QR Code" className="w-48 h-48 rounded-lg bg-white p-2" />
          {backupCodes.length > 0 && (
            <div>
              <p className="text-xs font-medium mb-1">Backup Codes (save these!):</p>
              <div className="grid grid-cols-2 gap-1">
                {backupCodes.map((c, i) => (
                  <code key={i} className="text-xs bg-white/[0.04] px-2 py-0.5 rounded font-mono">{c}</code>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
