# Phase 5 — Asset Library + Channel Collector

> **Goal**: Build 2 pages: `/assets` library + `/channel-collector` competitor research.
> **Effort**: 4 ngày
> **Risk**: MEDIUM
> **Prerequisite**: P1
> **Source**: `docs/HIDDEN-FEATURES-GAP-ANALYSIS.md` §3.1.D, §3.1.E

---

## 1. Vấn đề

### Asset Library
Backend có 6 endpoints:
- `GET /api/assets` — list user's assets (image, video, audio)
- `POST /api/assets` — create
- `GET /api/assets/{id}` — detail
- `PATCH /api/assets/{id}` — update metadata
- `DELETE /api/assets/{id}` — delete
- `POST /api/assets/search` — search by tags/type

Hiện user phải navigate qua từng project để xem assets → không có global library.

### Channel Collector
Backend có 5 endpoints:
- `POST /api/channel-collector/scrape` — start scraping channel
- `GET /api/channel-collector/jobs/{id}` — job status
- `GET /api/channel-collector/channels` — list tracked channels
- `POST /api/channel-collector/channels` — add channel
- `DELETE /api/channel-collector/channels/{id}` — remove

Không có UI page, dù backend đã implement.

## 2. Acceptance Criteria

### 2.1 Asset Library list page

- [ ] `/assets` route exists
- [ ] Grid/list view toggle
- [ ] Filter by: type (image/video/audio), tags, project
- [ ] Sort by: created date, name, size
- [ ] Click asset → detail page
- [ ] "Upload" button → POST /api/assets
- [ ] Multi-select → bulk delete

### 2.2 Asset detail page

- [ ] `/assets/[id]` route exists
- [ ] Preview asset (image/video/audio player)
- [ ] Metadata: name, tags, project, source, license, size, checksum
- [ ] Edit metadata
- [ ] Delete (with confirm)
- [ ] "Download" button
- [ ] "Use in project" button → add to project library

### 2.3 Channel Collector page

- [ ] `/channel-collector` route exists
- [ ] List tracked channels
- [ ] "Add channel" button → form (URL, name)
- [ ] Scraping jobs list with status
- [ ] Per-channel: latest scraped data (recent videos, comments count)
- [ ] Delete channel

### 2.4 Channel detail page

- [ ] `/channel-collector/[id]` route exists
- [ ] Channel metadata
- [ ] Recent videos list (clickable → opens detail)
- [ ] Top comments / insights
- [ ] "Re-scrape" button

### 2.5 Tests

- [ ] Component tests for asset grid + filter
- [ ] Integration tests for all endpoints
- [ ] E2E: upload asset → search → use in project

## 3. Implementation Outline

### 3.1 Asset library page

**File: `apps/web/app/(dashboard)/assets/page.tsx` (MỚI)**

```tsx
import { apiFetch } from "@/lib/api-client";
import { AssetGrid } from "@/components/asset-grid";
import { AssetFilters } from "@/components/asset-filters";

export default async function AssetsPage({ searchParams }) {
  const params = await searchParams;
  const token = await getAuthToken();
  const query = new URLSearchParams({
    type: params.type || "",
    tag: params.tag || "",
    sort: params.sort || "created_desc",
    page: params.page || "1",
  }).toString();
  const r = await apiFetch(`/api/assets?${query}`, { cache: "no-store" }, token);
  const { assets = [], total = 0 } = await r.json();

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Asset Library ({total})</h1>
        <button className="btn btn-primary">+ Upload Asset</button>
      </div>

      <AssetFilters />

      <AssetGrid assets={assets} />
    </div>
  );
}
```

### 3.2 Asset grid component

**File: `apps/web/components/asset-grid.tsx` (MỚI)**

```tsx
"use client";
import { useState } from "react";
import Link from "next/link";

interface Asset {
  id: string;
  name: string;
  type: "image" | "video" | "audio";
  storage_url: string;
  thumbnail_url?: string;
  size_bytes: number;
  tags: string[];
  created_at: string;
}

export function AssetGrid({ assets }: { assets: Asset[] }) {
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const toggleSelect = (id: string) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelected(next);
  };

  return (
    <div className="grid grid-cols-4 gap-4 mt-4">
      {assets.map((a) => (
        <div
          key={a.id}
          className={`border rounded p-2 hover:shadow ${selected.has(a.id) ? "ring-2 ring-blue-500" : ""}`}
          onClick={() => toggleSelect(a.id)}
        >
          <Link href={`/assets/${a.id}`}>
            {a.type === "image" ? (
              <img src={a.thumbnail_url || a.storage_url} alt={a.name} className="w-full h-32 object-cover" />
            ) : a.type === "video" ? (
              <video src={a.storage_url} className="w-full h-32 object-cover" />
            ) : (
              <div className="w-full h-32 bg-gray-100 flex items-center justify-center">🎵 Audio</div>
            )}
          </Link>
          <p className="mt-2 text-sm font-medium truncate">{a.name}</p>
          <p className="text-xs text-gray-500">
            {a.type} • {(a.size_bytes / 1024 / 1024).toFixed(1)}MB
          </p>
        </div>
      ))}
    </div>
  );
}
```

### 3.3 Channel Collector page

**File: `apps/web/app/(dashboard)/channel-collector/page.tsx` (MỚI)**

```tsx
import { apiFetch } from "@/lib/api-client";
import { ChannelList } from "@/components/channel-list";
import { ScrapeJobList } from "@/components/scrape-job-list";

export default async function ChannelCollectorPage() {
  const token = await getAuthToken();
  const [channelsRes, jobsRes] = await Promise.all([
    apiFetch("/api/channel-collector/channels", { cache: "no-store" }, token),
    apiFetch("/api/channel-collector/jobs", { cache: "no-store" }, token),
  ]);
  const { channels = [] } = await channelsRes.json();
  const { jobs = [] } = await jobsRes.json();

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Channel Collector</h1>

      <div className="grid grid-cols-2 gap-6">
        <div>
          <h2 className="text-lg font-semibold mb-2">Tracked Channels</h2>
          <ChannelList channels={channels} />
        </div>
        <div>
          <h2 className="text-lg font-semibold mb-2">Recent Jobs</h2>
          <ScrapeJobList jobs={jobs} />
        </div>
      </div>
    </div>
  );
}
```

## 4. Files thay đổi

| File | Action | LOC |
|---|---|---|
| `apps/web/app/(dashboard)/assets/page.tsx` | MỚI | +60 |
| `apps/web/app/(dashboard)/assets/[id]/page.tsx` | MỚI | +80 |
| `apps/web/app/(dashboard)/channel-collector/page.tsx` | MỚI | +50 |
| `apps/web/app/(dashboard)/channel-collector/[id]/page.tsx` | MỚI | +60 |
| `apps/web/components/asset-grid.tsx` | MỚI | +80 |
| `apps/web/components/asset-filters.tsx` | MỚI | +60 |
| `apps/web/components/asset-upload.tsx` | MỚI | +80 |
| `apps/web/components/asset-detail-actions.tsx` | MỚI | +50 |
| `apps/web/components/channel-list.tsx` | MỚI | +50 |
| `apps/web/components/channel-form.tsx` | MỚI | +60 |
| `apps/web/components/scrape-job-list.tsx` | MỚI | +50 |
| `tests/web/components/test_asset_grid.tsx` | MỚI | +50 |
| `tests/api/test_asset_endpoints.py` | MỚI | +40 |
| `tests/api/test_channel_collector.py` | MỚI | +40 |

## 5. Test plan

```bash
pytest tests/web/components/test_asset_grid.tsx -v
pytest tests/api/test_asset_endpoints.py -v
pytest tests/api/test_channel_collector.py -v
bash scripts/run_e2e_local.sh
```

## 6. Done when

- [ ] Asset library 2 pages (list, detail)
- [ ] Channel collector 2 pages (list, detail)
- [ ] Filters + sort work
- [ ] Upload + delete work
- [ ] Tests pass
- [ ] Coverage ≥80%
- [ ] Tier 1 sign-off