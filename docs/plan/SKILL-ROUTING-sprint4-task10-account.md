# Sprint 4+ Task Group 10: Account Settings - Skill Routing

## Commands ĐƯỢC PHÉP
- ✅ Read, Write, StrReplace (apps/web only)
- ✅ ReadLints

## Commands KHÔNG ĐƯỘC PHÉP
- ❌ Đổi Backend
- ❌ Đổi Tasks 1-9 code
- ❌ Launch subagents

## Patterns BẮT BUỘC

### 1. Profile Update Pattern

```typescript
'use client';
import { useState } from 'react';

export function ProfileForm({ initialData }: { initialData: any }) {
  const [fullName, setFullName] = useState(initialData.full_name || '');
  const [avatarUrl, setAvatarUrl] = useState(initialData.avatar_url || '');
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    const res = await fetch('/api/account/update-profile', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name: fullName, avatar_url: avatarUrl }),
    });
    if (res.ok) alert('Đã lưu');
    else alert('Lỗi');
    setSaving(false);
  }

  return (
    <div className="space-y-3">
      <input value={fullName} onChange={(e) => setFullName(e.target.value)} />
      <button onClick={handleSave} disabled={saving}>Save</button>
    </div>
  );
}
```

---

## Files CÓ THỂ TẠO
- ✅ `apps/web/app/account/settings/page.tsx`
- ✅ `apps/web/app/pricing/page.tsx`
- ✅ `apps/web/app/api/account/update-profile/route.ts`
- ✅ `apps/web/app/api/account/change-password/route.ts`
- ✅ `apps/web/components/profile-form.tsx`
- ✅ `apps/web/components/password-form.tsx`
- ✅ `apps/web/components/pricing-card.tsx`

## Files KHÔNG ĐƯỢC SỬA
- ❌ `apps/api/routers/users.py` (đã có update endpoint)
- ❌ Tasks 1-9 files