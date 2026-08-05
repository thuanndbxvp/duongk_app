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
