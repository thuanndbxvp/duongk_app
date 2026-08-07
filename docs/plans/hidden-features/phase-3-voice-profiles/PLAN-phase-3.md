# Phase 3 — Voice Profiles Page

> **Goal**: Build `/voice-profiles` page cho user tạo/list voice clone riêng.
> **Effort**: 4 ngày
> **Risk**: MEDIUM (TTS provider integration nuance)
> **Prerequisite**: P1
> **Source**: `docs/HIDDEN-FEATURES-GAP-ANALYSIS.md` §3.1.B, §5.2

---

## 1. Vấn đề

Backend có 8 endpoints cho voice profiles:
- `GET /api/voices` — list
- `POST /api/voices` — create
- `GET /api/voices/{id}` — detail
- `PATCH /api/voices/{id}` — update
- `DELETE /api/voices/{id}` — delete
- `POST /api/voices/{id}/clone` — clone từ sample audio
- `POST /api/voices/{id}/test` — generate sample audio
- `GET /api/voices/providers` — list supported providers

Nhưng KHÔNG có UI page. User không biết có thể tạo voice clone riêng.

## 2. Acceptance Criteria

### 2.1 List page

- [ ] Page `app/(dashboard)/voice-profiles/page.tsx` exists
- [ ] Server component fetches voices từ `GET /api/voices`
- [ ] Grid view (card per voice) với: name, provider, language, gender, sample audio player
- [ ] "New voice" button → navigate to `/voice-profiles/new`
- [ ] Loading state: skeleton cards
- [ ] Empty state: "Bạn chưa có voice nào" + CTA button

### 2.2 Create page

- [ ] Page `app/(dashboard)/voice-profiles/new/page.tsx` exists
- [ ] Form fields:
  - Name (text)
  - Provider (dropdown từ `GET /api/voices/providers`)
  - Language (dropdown)
  - Gender (radio)
  - Sample audio file (file input, MP3/WAV, max 10MB)
- [ ] Submit → POST `/api/voices` with multipart/form-data
- [ ] Server-side: validate file type, size, provider compatibility
- [ ] Success → redirect to detail page
- [ ] Error → show inline errors

### 2.3 Detail page

- [ ] Page `app/(dashboard)/voice-profiles/[id]/page.tsx`
- [ ] Show voice metadata + sample audio player
- [ ] "Test" button → POST `/api/voices/{id}/test` with text input → play generated audio
- [ ] "Edit" button → navigate to edit form
- [ ] "Delete" button → confirm dialog → DELETE
- [ ] "Clone" button → file input → POST `/api/voices/{id}/clone`

### 2.4 Backend provider list

- [ ] `GET /api/voices/providers` returns:
  ```json
  {
    "providers": [
      {
        "id": "omnivoice",
        "name": "OmniVoice",
        "languages": ["vi-VN", "en-US"],
        "supports_clone": true,
        "requires_sample": true
      },
      ...
    ]
  }
  ```
- [ ] Endpoint exists hoặc Tier 2 implement (low effort, just static data)

### 2.5 Tests

- [ ] Unit test: voice list page renders
- [ ] Unit test: form validation
- [ ] Integration test: POST /api/voices with multipart
- [ ] Integration test: POST /api/voices/{id}/test
- [ ] E2E: create voice → test → delete

## 3. Implementation Outline

### 3.1 List page

**File: `apps/web/app/(dashboard)/voice-profiles/page.tsx` (MỚI)**

```tsx
import { apiFetch } from "@/lib/api-client";
import { VoiceCard } from "@/components/voice-card";

export default async function VoiceProfilesPage() {
  const token = await getAuthToken();
  const r = await apiFetch("/api/voices", { cache: "no-store" }, token);
  const { voices = [] } = await r.json();

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Voice Profiles</h1>
        <Link href="/voice-profiles/new" className="btn btn-primary">
          + New Voice
        </Link>
      </div>

      {voices.length === 0 ? (
        <EmptyState
          title="Chưa có voice profile"
          description="Tạo voice clone riêng để sử dụng cho video"
          cta={<Link href="/voice-profiles/new" className="btn btn-primary">Tạo voice đầu tiên</Link>}
        />
      ) : (
        <div className="grid grid-cols-3 gap-4">
          {voices.map((v) => (
            <VoiceCard key={v.id} voice={v} />
          ))}
        </div>
      )}
    </div>
  );
}
```

### 3.2 VoiceCard component

**File: `apps/web/components/voice-card.tsx` (MỚI)**

```tsx
import Link from "next/link";

interface Voice {
  id: string;
  name: string;
  provider: string;
  language: string;
  gender: string;
  sample_url?: string;
}

export function VoiceCard({ voice }: { voice: Voice }) {
  return (
    <Link href={`/voice-profiles/${voice.id}`} className="border rounded-lg p-4 hover:shadow">
      <h3 className="font-semibold">{voice.name}</h3>
      <p className="text-sm text-gray-600">
        {voice.provider} • {voice.language} • {voice.gender}
      </p>
      {voice.sample_url && (
        <audio controls className="w-full mt-2">
          <source src={voice.sample_url} />
        </audio>
      )}
    </Link>
  );
}
```

### 3.3 Create form

**File: `apps/web/app/(dashboard)/voice-profiles/new/page.tsx` (MỚI)**

```tsx
import { VoiceForm } from "@/components/voice-form";

export default async function NewVoicePage() {
  const token = await getAuthToken();
  const r = await apiFetch("/api/voices/providers", { cache: "no-store" }, token);
  const { providers = [] } = await r.json();

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Tạo Voice Profile mới</h1>
      <VoiceForm providers={providers} />
    </div>
  );
}
```

**File: `apps/web/components/voice-form.tsx` (MỚI)**

```tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

interface Provider {
  id: string;
  name: string;
  languages: string[];
  supports_clone: boolean;
  requires_sample: boolean;
}

export function VoiceForm({ providers }: { providers: Provider[] }) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [providerId, setProviderId] = useState(providers[0]?.id || "");
  const [language, setLanguage] = useState("");
  const [gender, setGender] = useState("neutral");
  const [sample, setSample] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const provider = providers.find((p) => p.id === providerId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!sample && provider?.requires_sample) {
      setError("Provider này yêu cầu sample audio");
      return;
    }
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append("name", name);
      formData.append("provider_id", providerId);
      formData.append("language", language);
      formData.append("gender", gender);
      if (sample) formData.append("sample", sample);

      const r = await fetch("/api/voices", {
        method: "POST",
        body: formData,
      });
      if (!r.ok) throw new Error(await r.text());
      const { id } = await r.json();
      router.push(`/voice-profiles/${id}`);
    } catch (e) {
      setError((e as Error).message);
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <div className="alert alert-error">{error}</div>}
      <div>
        <label className="block mb-1">Tên voice</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          className="w-full border rounded px-3 py-2"
        />
      </div>
      <div>
        <label className="block mb-1">Provider</label>
        <select
          value={providerId}
          onChange={(e) => {
            setProviderId(e.target.value);
            const p = providers.find((p) => p.id === e.target.value);
            if (p) setLanguage(p.languages[0] || "");
          }}
          className="w-full border rounded px-3 py-2"
        >
          {providers.map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="block mb-1">Ngôn ngữ</label>
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="w-full border rounded px-3 py-2"
        >
          {provider?.languages.map((l) => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="block mb-1">Giới tính</label>
        <div className="flex gap-4">
          {["male", "female", "neutral"].map((g) => (
            <label key={g} className="flex items-center">
              <input
                type="radio"
                name="gender"
                value={g}
                checked={gender === g}
                onChange={() => setGender(g)}
              />
              <span className="ml-2 capitalize">{g}</span>
            </label>
          ))}
        </div>
      </div>
      <div>
        <label className="block mb-1">Sample audio (MP3/WAV, max 10MB)</label>
        <input
          type="file"
          accept="audio/mpeg,audio/wav"
          onChange={(e) => setSample(e.target.files?.[0] || null)}
          required={provider?.requires_sample}
        />
      </div>
      <button type="submit" disabled={isLoading} className="btn btn-primary">
        {isLoading ? "Đang upload..." : "Tạo voice"}
      </button>
    </form>
  );
}
```

### 3.4 Detail + test page

**File: `apps/web/app/(dashboard)/voice-profiles/[id]/page.tsx` (MỚI)**

```tsx
import { apiFetch } from "@/lib/api-client";
import { VoiceDetailActions } from "@/components/voice-detail-actions";

export default async function VoiceDetailPage({ params }) {
  const { id } = await params;
  const token = await getAuthToken();
  const r = await apiFetch(`/api/voices/${id}`, { cache: "no-store" }, token);
  const voice = await r.json();

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold">{voice.name}</h1>
      <p className="text-gray-600">{voice.provider} • {voice.language} • {voice.gender}</p>

      {voice.sample_url && (
        <div className="mt-4">
          <h3>Sample</h3>
          <audio controls src={voice.sample_url} className="w-full" />
        </div>
      )}

      <VoiceDetailActions voice={voice} />
    </div>
  );
}
```

**File: `apps/web/components/voice-detail-actions.tsx` (MỚI)**

```tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export function VoiceDetailActions({ voice }) {
  const router = useRouter();
  const [testText, setTestText] = useState("Xin chào, đây là test voice.");
  const [testAudioUrl, setTestAudioUrl] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleTest = async () => {
    setIsLoading(true);
    try {
      const r = await fetch(`/api/voices/${voice.id}/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: testText }),
      });
      if (!r.ok) throw new Error(await r.text());
      const { audio_url } = await r.json();
      setTestAudioUrl(audio_url);
    } catch (e) {
      alert("Lỗi: " + (e as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Xóa voice này?")) return;
    await fetch(`/api/voices/${voice.id}`, { method: "DELETE" });
    router.push("/voice-profiles");
  };

  return (
    <div className="mt-6 space-y-4">
      <div>
        <h3>Test voice</h3>
        <textarea
          value={testText}
          onChange={(e) => setTestText(e.target.value)}
          rows={3}
          className="w-full border rounded px-3 py-2"
        />
        <button onClick={handleTest} disabled={isLoading} className="btn btn-secondary mt-2">
          {isLoading ? "Đang generate..." : "Test"}
        </button>
        {testAudioUrl && (
          <audio controls src={testAudioUrl} className="w-full mt-2" />
        )}
      </div>
      <div className="flex gap-2">
        <button onClick={() => router.push(`/voice-profiles/${voice.id}/edit`)} className="btn">
          Edit
        </button>
        <button onClick={handleDelete} className="btn btn-danger">Delete</button>
      </div>
    </div>
  );
}
```

## 4. Files thay đổi

| File | Action | LOC |
|---|---|---|
| `apps/web/app/(dashboard)/voice-profiles/page.tsx` | MỚI | +50 |
| `apps/web/app/(dashboard)/voice-profiles/new/page.tsx` | MỚI | +30 |
| `apps/web/app/(dashboard)/voice-profiles/[id]/page.tsx` | MỚI | +40 |
| `apps/web/components/voice-card.tsx` | MỚI | +30 |
| `apps/web/components/voice-form.tsx` | MỚI | +120 |
| `apps/web/components/voice-detail-actions.tsx` | MỚI | +80 |
| `apps/api/modules/voices/routes.py` | SỬA (add /providers) | +30 |
| `tests/web/components/test_voice_form.tsx` | MỚI | +50 |
| `tests/api/test_voices_endpoints.py` | MỚI | +60 |

## 5. Test plan

```bash
pytest tests/web/components/test_voice_form.tsx -v
pytest tests/api/test_voices_endpoints.py -v
bash scripts/run_e2e_local.sh
```

## 6. Done when

- [ ] 3 pages exist (list, new, detail)
- [ ] Form validation works
- [ ] POST /api/voices with multipart works
- [ ] Test endpoint works
- [ ] All tests pass
- [ ] Coverage ≥80%
- [ ] Tier 1 sign-off