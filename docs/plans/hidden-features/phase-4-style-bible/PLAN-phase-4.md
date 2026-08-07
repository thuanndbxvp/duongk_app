# Phase 4 — Style Bible UI

> **Goal**: Build `/style-bible` page cho user quản lý visual style guide cho project (colors, typography, character refs).
> **Effort**: 5 ngày
> **Risk**: MEDIUM (multi-section form, complex state)
> **Prerequisite**: P2 (analysis tabs wire xong, vì Style Bible dùng analysis output làm input)
> **Source**: `docs/HIDDEN-FEATURES-GAP-ANALYSIS.md` §3.1.C, §4.B

---

## 1. Vấn đề

Backend đã implement Style Bible (visual style guide) từ Phase 9 nhưng không có UI:

| Endpoint | Purpose |
|---|---|
| `GET /api/style-bibles` | List user's style bibles |
| `POST /api/style-bibles` | Create new |
| `GET /api/style-bibles/{id}` | Detail |
| `PATCH /api/style-bibles/{id}` | Update |
| `DELETE /api/style-bibles/{id}` | Delete |
| `POST /api/style-bibles/{id}/sections` | Add section (color, typography, character) |
| `GET /api/style-bibles/{id}/preview` | Generate preview image |

## 2. Acceptance Criteria

### 2.1 List page

- [ ] Page `/style-bibles`
- [ ] Grid view với style bible cards (preview image + name)
- [ ] "New style bible" button
- [ ] Empty state
- [ ] Search/filter by tags

### 2.2 Detail page

- [ ] Page `/style-bibles/[id]`
- [ ] Show all sections:
  - **Colors** — palette swatches với hex codes
  - **Typography** — font previews
  - **Characters** — character refs với images
  - **Backgrounds** — bg refs với images
- [ ] Add/edit/delete section inline
- [ ] "Preview" button → generate preview image
- [ ] "Apply to project" button → pick project + apply

### 2.3 Create form

- [ ] Page `/style-bibles/new`
- [ ] Form: name, description, tags
- [ ] Submit → create blank bible
- [ ] Redirect to detail page to add sections

### 2.4 Tests

- [ ] Unit tests for components
- [ ] Integration tests for endpoints
- [ ] E2E: create bible → add color → add char → preview

## 3. Implementation Outline

### 3.1 List page

**File: `apps/web/app/(dashboard)/style-bibles/page.tsx` (MỚI)**

```tsx
import { apiFetch } from "@/lib/api-client";
import { StyleBibleCard } from "@/components/style-bible-card";
import Link from "next/link";

export default async function StyleBiblesPage({ searchParams }) {
  const params = await searchParams;
  const search = params.search || "";
  const token = await getAuthToken();
  const r = await apiFetch(`/api/style-bibles?search=${search}`, { cache: "no-store" }, token);
  const { bibles = [] } = await r.json();

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Style Bibles</h1>
        <Link href="/style-bibles/new" className="btn btn-primary">+ New Style Bible</Link>
      </div>

      <input
        type="search"
        placeholder="Search by name or tag..."
        defaultValue={search}
        className="w-full mb-4 px-3 py-2 border rounded"
      />

      {bibles.length === 0 ? (
        <p className="text-center text-gray-500 py-12">Chưa có style bible nào</p>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          {bibles.map((b) => <StyleBibleCard key={b.id} bible={b} />)}
        </div>
      )}
    </div>
  );
}
```

### 3.2 Detail page (multi-section)

**File: `apps/web/app/(dashboard)/style-bibles/[id]/page.tsx` (MỚI)**

```tsx
import { apiFetch } from "@/lib/api-client";
import { StyleBibleDetail } from "@/components/style-bible-detail";

export default async function StyleBibleDetailPage({ params }) {
  const { id } = await params;
  const token = await getAuthToken();
  const r = await apiFetch(`/api/style-bibles/${id}`, { cache: "no-store" }, token);
  const bible = await r.json();

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold">{bible.name}</h1>
      <p className="text-gray-600">{bible.description}</p>

      <StyleBibleDetail bible={bible} />
    </div>
  );
}
```

**File: `apps/web/components/style-bible-detail.tsx` (MỚI)**

```tsx
"use client";
import { useState } from "react";

export function StyleBibleDetail({ bible }) {
  const [sections, setSections] = useState(bible.sections || []);

  const handleAddSection = async (type: string, data: any) => {
    const r = await fetch(`/api/style-bibles/${bible.id}/sections`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type, data }),
    });
    if (r.ok) {
      const section = await r.json();
      setSections([...sections, section]);
    }
  };

  const handlePreview = async () => {
    const r = await fetch(`/api/style-bibles/${bible.id}/preview`, { method: "POST" });
    const { preview_url } = await r.json();
    window.open(preview_url, "_blank");
  };

  return (
    <div className="mt-6 space-y-6">
      {/* Colors section */}
      <Section title="Colors">
        <ColorPalette
          colors={sections.filter(s => s.type === "color")}
          onAdd={(hex, name) => handleAddSection("color", { hex, name })}
        />
      </Section>

      {/* Typography */}
      <Section title="Typography">
        <TypographyList
          items={sections.filter(s => s.type === "typography")}
          onAdd={(font, weight) => handleAddSection("typography", { font, weight })}
        />
      </Section>

      {/* Characters */}
      <Section title="Characters">
        <CharacterRefs
          refs={sections.filter(s => s.type === "character")}
          onAdd={(name, imageUrl) => handleAddSection("character", { name, image_url: imageUrl })}
        />
      </Section>

      {/* Backgrounds */}
      <Section title="Backgrounds">
        <BackgroundRefs
          refs={sections.filter(s => s.type === "background")}
          onAdd={(name, imageUrl) => handleAddSection("background", { name, image_url: imageUrl })}
        />
      </Section>

      <div className="flex gap-2">
        <button onClick={handlePreview} className="btn btn-primary">Generate Preview</button>
        <button onClick={() => alert("Apply to project - TODO")} className="btn">
          Apply to Project
        </button>
      </div>
    </div>
  );
}
```

### 3.3 Color palette component

**File: `apps/web/components/color-palette.tsx` (MỚI)**

```tsx
"use client";
import { useState } from "react";

interface ColorSection {
  id: string;
  type: "color";
  data: { hex: string; name: string };
}

export function ColorPalette({ colors, onAdd }: { colors: ColorSection[]; onAdd: (hex: string, name: string) => void }) {
  const [hex, setHex] = useState("#3b82f6");
  const [name, setName] = useState("");

  return (
    <div>
      <div className="flex gap-2 mb-4">
        {colors.map((c) => (
          <div key={c.id} className="text-center">
            <div style={{ background: c.data.hex }} className="w-16 h-16 rounded shadow" />
            <p className="text-xs mt-1">{c.data.name}</p>
            <code className="text-xs">{c.data.hex}</code>
          </div>
        ))}
      </div>
      <div className="flex gap-2 items-end">
        <input type="color" value={hex} onChange={(e) => setHex(e.target.value)} />
        <input
          type="text"
          placeholder="Color name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="border rounded px-2 py-1"
        />
        <button
          onClick={() => { onAdd(hex, name); setName(""); }}
          className="btn btn-secondary"
        >
          + Add
        </button>
      </div>
    </div>
  );
}
```

## 4. Files thay đổi

| File | Action | LOC |
|---|---|---|
| `apps/web/app/(dashboard)/style-bibles/page.tsx` | MỚI | +50 |
| `apps/web/app/(dashboard)/style-bibles/new/page.tsx` | MỚI | +40 |
| `apps/web/app/(dashboard)/style-bibles/[id]/page.tsx` | MỚI | +30 |
| `apps/web/components/style-bible-card.tsx` | MỚI | +30 |
| `apps/web/components/style-bible-detail.tsx` | MỚI | +120 |
| `apps/web/components/color-palette.tsx` | MỚI | +50 |
| `apps/web/components/typography-list.tsx` | MỚI | +50 |
| `apps/web/components/character-refs.tsx` | MỚI | +50 |
| `apps/web/components/background-refs.tsx` | MỚI | +50 |
| `apps/web/components/section.tsx` | MỚI | +20 |
| `tests/web/components/test_style_bible.tsx` | MỚI | +80 |
| `tests/api/test_style_bible_endpoints.py` | MỚI | +60 |

## 5. Test plan

```bash
pytest tests/web/components/test_style_bible.tsx -v
pytest tests/api/test_style_bible_endpoints.py -v
bash scripts/run_e2e_local.sh
```

## 6. Done when

- [ ] 3 pages (list, new, detail)
- [ ] 4 section types (color, typography, character, background)
- [ ] Preview generation works
- [ ] All tests pass
- [ ] Coverage ≥80%
- [ ] Tier 1 sign-off