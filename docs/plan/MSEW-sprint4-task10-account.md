# Sprint 4+ Task Group 10: Account Settings - MSEW

## Checklist

- [ ] Bước 1: API proxy for update-profile
- [ ] Bước 2: API proxy for change-password
- [ ] Bước 3: ProfileForm component
- [ ] Bước 4: PasswordForm component
- [ ] Bước 5: PricingCard component
- [ ] Bước 6: Account settings page
- [ ] Bước 7: Pricing page
- [ ] Bước 8: Verify

---

## Bước 1: Update Profile API

**File:** `apps/web/app/api/account/update-profile/route.ts`

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function PATCH(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await req.json();

  try {
    const response = await apiFetch(
      '/api/users/me',
      {
        method: 'PATCH',
        body: JSON.stringify(body),
      },
      token
    );
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

---

## Bước 2: Change Password API

**File:** `apps/web/app/api/account/change-password/route.ts`

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { getAccessToken } from '@/lib/auth';

export async function POST(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await req.json();

  // Validate
  if (!body.new_password || body.new_password.length < 8) {
    return NextResponse.json(
      { error: 'Password must be at least 8 characters' },
      { status: 400 }
    );
  }

  if (body.new_password !== body.confirm_password) {
    return NextResponse.json(
      { error: 'Passwords do not match' },
      { status: 400 }
    );
  }

  try {
    // Call Supabase Auth update user endpoint
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_SUPABASE_URL}/auth/v1/user`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          apikey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        },
        body: JSON.stringify({
          password: body.new_password,
        }),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.message || 'Failed to update password' },
        { status: response.status }
      );
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

---

## Bước 3: ProfileForm

**File:** `apps/web/components/profile-form.tsx`

```typescript
'use client';

import { useState } from 'react';

interface Props {
  initial: {
    email: string;
    full_name: string | null;
    avatar_url: string | null;
  };
}

export function ProfileForm({ initial }: Props) {
  const [fullName, setFullName] = useState(initial.full_name || '');
  const [avatarUrl, setAvatarUrl] = useState(initial.avatar_url || '');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage('');

    try {
      const res = await fetch('/api/account/update-profile', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: fullName,
          avatar_url: avatarUrl,
        }),
      });

      if (res.ok) {
        setMessage('✅ Đã lưu thay đổi');
      } else {
        const err = await res.json();
        setMessage(`❌ ${err.error || 'Lỗi'}`);
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSave} className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-1">Email</label>
        <input
          type="email"
          value={initial.email}
          disabled
          className="w-full p-2 border rounded bg-gray-100 cursor-not-allowed"
        />
        <p className="text-xs text-gray-500 mt-1">
          Email không thể thay đổi
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Họ và tên</label>
        <input
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          className="w-full p-2 border rounded"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Avatar URL</label>
        <input
          type="url"
          value={avatarUrl}
          onChange={(e) => setAvatarUrl(e.target.value)}
          placeholder="https://..."
          className="w-full p-2 border rounded"
        />
      </div>

      {message && (
        <p className={`text-sm ${message.startsWith('✅') ? 'text-green-600' : 'text-red-600'}`}>
          {message}
        </p>
      )}

      <button
        type="submit"
        disabled={saving}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {saving ? 'Đang lưu...' : 'Lưu thay đổi'}
      </button>
    </form>
  );
}
```

---

## Bước 4: PasswordForm

**File:** `apps/web/components/password-form.tsx`

```typescript
'use client';

import { useState } from 'react';

export function PasswordForm() {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMessage('');

    if (newPassword.length < 8) {
      setMessage('❌ Mật khẩu mới phải có ít nhất 8 ký tự');
      return;
    }

    if (newPassword !== confirmPassword) {
      setMessage('❌ Mật khẩu xác nhận không khớp');
      return;
    }

    setSaving(true);

    try {
      const res = await fetch('/api/account/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
          confirm_password: confirmPassword,
        }),
      });

      if (res.ok) {
        setMessage('✅ Đã đổi mật khẩu');
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
      } else {
        const err = await res.json();
        setMessage(`❌ ${err.error || 'Lỗi'}`);
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-1">Mật khẩu hiện tại</label>
        <input
          type="password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          required
          className="w-full p-2 border rounded"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Mật khẩu mới</label>
        <input
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          required
          minLength={8}
          className="w-full p-2 border rounded"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Xác nhận mật khẩu mới</label>
        <input
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
          className="w-full p-2 border rounded"
        />
      </div>

      {message && (
        <p className={`text-sm ${message.startsWith('✅') ? 'text-green-600' : 'text-red-600'}`}>
          {message}
        </p>
      )}

      <button
        type="submit"
        disabled={saving}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {saving ? 'Đang cập nhật...' : 'Đổi mật khẩu'}
      </button>
    </form>
  );
}
```

---

## Bước 5: PricingCard

**File:** `apps/web/components/pricing-card.tsx`

```typescript
'use client';

interface Props {
  tier: 'free' | 'pro' | 'enterprise';
  name: string;
  price: string;
  credits: number;
  features: string[];
  currentTier: string;
  onUpgrade?: () => void;
  popular?: boolean;
}

export function PricingCard({
  tier,
  name,
  price,
  credits,
  features,
  currentTier,
  onUpgrade,
  popular,
}: Props) {
  const isCurrent = currentTier === tier;

  return (
    <div
      className={`relative bg-white rounded-lg shadow border p-6 ${
        popular ? 'border-blue-500 ring-2 ring-blue-200' : ''
      }`}
    >
      {popular && (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-600 text-white px-3 py-1 rounded-full text-xs font-bold">
          ⭐ POPULAR
        </span>
      )}

      <h3 className="text-2xl font-bold">{name}</h3>
      <p className="text-4xl font-bold mt-2">
        {price}
        <span className="text-sm text-gray-500 font-normal">/tháng</span>
      </p>

      <p className="text-sm text-gray-600 mt-2">
        💰 {credits} credits/tháng
      </p>

      <ul className="mt-4 space-y-2">
        {features.map((f, i) => (
          <li key={i} className="flex items-start gap-2 text-sm">
            <span className="text-green-500">✓</span>
            <span>{f}</span>
          </li>
        ))}
      </ul>

      <div className="mt-6">
        {isCurrent ? (
          <button
            disabled
            className="w-full bg-gray-200 text-gray-500 px-4 py-2 rounded cursor-not-allowed"
          >
            Plan hiện tại
          </button>
        ) : (
          <button
            onClick={onUpgrade}
            className={`w-full px-4 py-2 rounded font-medium ${
              popular
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
            }`}
          >
            {tier === 'enterprise' ? 'Liên hệ' : 'Upgrade'}
          </button>
        )}
      </div>
    </div>
  );
}
```

---

## Bước 6: Account Settings Page

**File:** `apps/web/app/account/settings/page.tsx`

```typescript
import { redirect } from 'next/navigation';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { ProfileForm } from '@/components/profile-form';
import { PasswordForm } from '@/components/password-form';

export default async function AccountSettingsPage() {
  const token = await getAccessToken();
  if (!token) redirect('/login');

  const res = await apiFetch('/api/users/me', {}, token);
  if (!res.ok) redirect('/login');

  const user = await res.json();

  return (
    <main className="container mx-auto p-8 max-w-2xl">
      <h1 className="text-3xl font-bold mb-8">Account Settings</h1>

      <div className="space-y-6">
        {/* Profile */}
        <section className="bg-white rounded-lg shadow border p-6">
          <h2 className="text-xl font-bold mb-4">Profile</h2>
          <ProfileForm
            initial={{
              email: user.email,
              full_name: user.full_name,
              avatar_url: user.avatar_url,
            }}
          />
        </section>

        {/* Security */}
        <section className="bg-white rounded-lg shadow border p-6">
          <h2 className="text-xl font-bold mb-4">Security</h2>
          <PasswordForm />
        </section>

        {/* Danger Zone */}
        <section className="bg-white rounded-lg shadow border border-red-300 p-6">
          <h2 className="text-xl font-bold mb-2 text-red-600">Danger Zone</h2>
          <p className="text-sm text-gray-600 mb-4">
            Xóa tài khoản sẽ xóa tất cả dữ liệu vĩnh viễn. Hành động này không thể hoàn tác.
          </p>
          <button
            onClick={() => {
              if (confirm('Bạn chắc chắn muốn xóa tài khoản?')) {
                alert('Liên hệ support@appdk.vn để xóa tài khoản.');
              }
            }}
            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Xóa tài khoản
          </button>
        </section>
      </div>
    </main>
  );
}
```

---

## Bước 7: Pricing Page

**File:** `apps/web/app/pricing/page.tsx`

```typescript
import { redirect } from 'next/navigation';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';
import { PricingCard } from '@/components/pricing-card';

export default async function PricingPage() {
  const token = await getAccessToken();
  // Pricing có thể public, nhưng cần current tier để highlight
  let currentTier = 'free';

  if (token) {
    const res = await apiFetch('/api/credits/balance', {}, token);
    if (res.ok) {
      const data = await res.json();
      currentTier = data.tier;
    }
  }

  const tiers = [
    {
      tier: 'free' as const,
      name: 'Free',
      price: '$0',
      credits: 100,
      features: [
        'Validate niche',
        'Collect 50 videos',
        'Generate 2 scripts/month',
        'Basic support',
      ],
    },
    {
      tier: 'pro' as const,
      name: 'Pro',
      price: '$19',
      credits: 500,
      features: [
        'Tất cả Free features',
        'Deep Analysis đầy đủ 14 outputs',
        'Generate 20 scripts/month',
        'Idea Generation unlimited',
        'Email support',
        'Priority queue',
      ],
      popular: true,
    },
    {
      tier: 'enterprise' as const,
      name: 'Enterprise',
      price: 'Custom',
      credits: 5000,
      features: [
        'Tất cả Pro features',
        '5000 credits/tháng',
        'Dedicated support 24/7',
        'Custom integrations',
        'SLA 99.9%',
      ],
    },
  ];

  function handleUpgrade(tier: string) {
    if (tier === 'enterprise') {
      window.location.href = 'mailto:sales@appdk.vn';
    } else {
      alert(`Upgrade to ${tier} - Tính năng thanh toán đang phát triển`);
    }
  }

  return (
    <main className="container mx-auto p-8 max-w-6xl">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-2">Choose Your Plan</h1>
        <p className="text-gray-600">
          Bắt đầu miễn phí, nâng cấp khi cần thiết
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {tiers.map((t) => (
          <PricingCard
            key={t.tier}
            tier={t.tier}
            name={t.name}
            price={t.price}
            credits={t.credits}
            features={t.features}
            currentTier={currentTier}
            popular={t.popular}
            onUpgrade={() => handleUpgrade(t.tier)}
          />
        ))}
      </div>
    </main>
  );
}
```

---

## Bước 8: Verify

```bash
cd apps/web
pnpm dev
# Navigate http://localhost:3000/account/settings
# Navigate http://localhost:3000/pricing
```

---

## Commands for Tier 2

```bash
cat docs/plan/CONTEXT-sprint4-task10-account.md
cat docs/plan/SKILL-ROUTING-sprint4-task10-account.md
cat docs/plan/PLAN-sprint4-task10-account.md
cat docs/plan/MSEW-sprint4-task10-account.md
cat docs/plan/ACCEPTANCE-sprint4-task10-account.md
```