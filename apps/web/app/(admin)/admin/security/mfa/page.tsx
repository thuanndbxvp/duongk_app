'use client';

import { useEffect, useState } from 'react';

type MfaStatus = 'not_enrolled' | 'pending' | 'active' | 'disabled';

interface EnrollmentData {
  secret: string;
  qr_uri: string;
  qr_png_base64: string;
  backup_codes: string[];
}

export default function AdminMfaPage() {
  const [status, setStatus] = useState<MfaStatus>('not_enrolled');
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [enrollment, setEnrollment] = useState<EnrollmentData | null>(null);
  const [verifyCode, setVerifyCode] = useState('');
  const [disableCode, setDisableCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/admin/mfa').then(r => r.json()).then(d => {
      setStatus(d.status);
      setLoading(false);
    });
  }, []);

  async function handleEnroll() {
    setError('');
    const res = await fetch('/api/admin/mfa/enroll', { method: 'POST' });
    if (res.ok) {
      setEnrollment(await res.json());
      setStep(2);
      setStatus('pending');
    } else {
      setError('Enroll failed');
    }
  }

  async function handleVerify() {
    setError('');
    const res = await fetch('/api/admin/mfa/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: verifyCode }),
    });
    if (res.ok) {
      setStep(3);
      setStatus('active');
    } else {
      const err = await res.json();
      setError(err.detail || 'Invalid code');
    }
  }

  async function handleDisable() {
    setError('');
    const res = await fetch('/api/admin/mfa/disable', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: disableCode }),
    });
    if (res.ok) {
      setStatus('disabled');
      setStep(1);
      setEnrollment(null);
      setDisableCode('');
    } else {
      const err = await res.json();
      setError(err.detail);
    }
  }

  if (loading) return <div className="p-8 text-center text-[var(--fg-tertiary)]">Loading…</div>;

  return (
    <div className="p-8 space-y-6 animate-fade-up max-w-3xl">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          Admin · Security
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">Multi-Factor Auth</span>
        </h1>
        <p className="text-[var(--fg-secondary)]">Bảo vệ tài khoản super_admin bằng TOTP (Google Authenticator / 1Password).</p>
      </div>

      {/* Status banner */}
      <div className={`glass rounded-2xl p-5 border-l-4 ${
        status === 'active' ? 'border-green-500' :
        status === 'pending' ? 'border-orange-500' :
        status === 'disabled' ? 'border-red-500' : 'border-blue-500'
      }`}>
        <p className="text-sm">
          Status: <strong>{status === 'active' ? '✓ Active' : status === 'pending' ? '⏳ Pending' : status === 'disabled' ? '✗ Disabled' : '○ Not enrolled'}</strong>
        </p>
        {status === 'active' && (
          <button onClick={() => setStep(1)} className="mt-3 text-sm text-red-400 underline">
            Disable MFA
          </button>
        )}
      </div>

      {error && <div className="glass rounded-xl p-3 text-sm text-red-400">{error}</div>}

      {/* Step 1: Setup */}
      {step === 1 && status !== 'active' && (
        <div className="glass rounded-2xl p-6 space-y-4">
          <h2 className="text-xl font-bold">Setup MFA</h2>
          <ol className="space-y-2 text-sm text-[var(--fg-secondary)]">
            <li>1. Cài <strong>Google Authenticator</strong> hoặc <strong>1Password</strong></li>
            <li>2. Click "Generate QR Code" bên dưới</li>
            <li>3. Scan QR → app hiển thị 6-digit code</li>
            <li>4. Nhập code → verify</li>
            <li>5. Save 10 backup codes ở nơi an toàn</li>
          </ol>
          <button onClick={handleEnroll} className="w-full px-4 py-3 rounded-lg bg-[var(--brand-500)] text-white font-semibold">
            Generate QR Code
          </button>
        </div>
      )}

      {/* Step 1 disable: input code */}
      {step === 1 && status === 'active' && (
        <div className="glass rounded-2xl p-6 space-y-4">
          <h2 className="text-xl font-bold text-red-400">Disable MFA</h2>
          <p className="text-sm text-[var(--fg-secondary)]">Nhập TOTP code hiện tại để xác nhận disable:</p>
          <input type="text" value={disableCode} onChange={(e) => setDisableCode(e.target.value)} maxLength={8}
            placeholder="123456 (TOTP) hoặc ABCD2345 (backup)"
            className="w-full px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white placeholder:text-[var(--fg-tertiary)]" />
          <button onClick={handleDisable} className="w-full px-4 py-3 rounded-lg bg-red-500 text-white font-semibold">
            Disable MFA
          </button>
        </div>
      )}

      {/* Step 2: Scan QR + verify */}
      {step === 2 && enrollment && (
        <div className="glass rounded-2xl p-6 space-y-4">
          <h2 className="text-xl font-bold">Scan QR Code</h2>
          <div className="flex justify-center bg-white p-4 rounded-lg">
            <img src={`data:image/png;base64,${enrollment.qr_png_base64}`} alt="MFA QR" className="w-64 h-64" />
          </div>
          <details className="text-xs">
            <summary className="cursor-pointer text-[var(--fg-tertiary)]">Không scan được? Hiển thị secret key</summary>
            <code className="block mt-2 p-2 bg-[var(--surface)] rounded font-mono break-all">{enrollment.secret}</code>
          </details>
          <hr className="border-[var(--glass-border)]" />
          <h3 className="font-semibold">Nhập 6-digit code từ authenticator:</h3>
          <input type="text" value={verifyCode} onChange={(e) => setVerifyCode(e.target.value)} maxLength={6}
            placeholder="123456"
            className="w-full px-3 py-3 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white text-center text-2xl tracking-widest placeholder:text-[var(--fg-tertiary)]" />
          <button onClick={handleVerify} disabled={verifyCode.length !== 6}
            className="w-full px-4 py-3 rounded-lg bg-[var(--brand-500)] text-white font-semibold disabled:opacity-30">
            Verify
          </button>
        </div>
      )}

      {/* Step 3: Save backup codes */}
      {step === 3 && enrollment && (
        <div className="glass rounded-2xl p-6 space-y-4 border-l-4 border-green-500">
          <h2 className="text-xl font-bold text-green-400">✓ MFA Active</h2>
          <p className="text-sm text-[var(--fg-secondary)]">Save 10 backup codes sau. Mỗi code dùng 1 lần khi mất authenticator.</p>
          <div className="grid grid-cols-2 gap-2 bg-[var(--surface)] rounded-lg p-4">
            {enrollment.backup_codes.map((code, i) => (
              <code key={i} className="font-mono text-sm text-[var(--brand-300)]">{code}</code>
            ))}
          </div>
          <button onClick={() => {
            navigator.clipboard.writeText(enrollment.backup_codes.join('\n'));
            alert('Copied!');
          }} className="w-full px-4 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)] text-white text-sm">
            📋 Copy all
          </button>
          <button onClick={() => { setEnrollment(null); setStep(1); }} className="w-full px-4 py-3 rounded-lg bg-green-500 text-white font-semibold">
            Done — đã save
          </button>
        </div>
      )}
    </div>
  );
}