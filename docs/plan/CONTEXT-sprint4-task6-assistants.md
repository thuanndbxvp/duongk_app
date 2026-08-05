# Sprint 4+ Task Group 6: Channel Assistants List & Detail

## 1. Context & Mục đích

### Bối cảnh

Sau khi user thu thập YouTube channel (Module 2a), hệ thống tự động tạo **Channel Assistant** - đây là "DNA" của kênh (phong cách, giọng nói, mimic rules). UI hiện tại KHÔNG có trang list/detail Assistant.

### Mục đích task group này

- Hiển thị **danh sách Channel Assistants** của user
- Trang **chi tiết Assistant** (metadata + channel info)
- **Navigate** từ Assistant → Analysis / Ideas / Scripts
- Bổ sung **API proxy routes** để enforce BFF pattern

### Mục tiêu UI

- `/assistants` - List tất cả Channel Assistants của user
- `/assistants/[id]` - Chi tiết Assistant + 4 action buttons (Analyze / Ideas / Script / History)

### Phụ thuộc

- ✅ Task 1: User & RLS (JWT user_id)
- ✅ Task 2: Next.js BFF (cookie session)
- ✅ Backend: `channel_assistants` table đã có (migration 0008)
- ✅ Backend: `/api/collect/channel` endpoint đã có

---

## 2. Data Model

### channel_assistants (Sprint 1)

```sql
CREATE TABLE channel_assistants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  channel_id TEXT NOT NULL,
  channel_name TEXT,
  channel_thumbnail TEXT,
  channel_subscribers INT,
  total_videos_collected INT,
  quality_videos_count INT,
  viral_videos_count INT,
  status TEXT DEFAULT 'collecting',  -- collecting / ready / failed
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### UI Derivable Fields

- `total_jobs` - count jobs where input_payload->>'assistant_id' = assistant.id
- `last_job_at` - max(created_at) của jobs
- `has_analysis` - boolean (channel_deep_analysis row exists)
- `has_scripts` - boolean (generated_scripts count > 0)

---

## 3. Pages to Build

| Page | Route | Purpose |
|------|-------|---------|
| Assistants List | `/assistants` | Grid view tất cả Channel DNA |
| Assistant Detail | `/assistants/[id]` | Detail + action buttons |

---

## 4. UI Layout

### /assistants

```
┌──────────────────────────────────────────────────────────────────┐
│  HEADER: Logo | Credits: 87 | Tier: Pro | Logout                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Channel Assistants (3)                                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                 │
│  │ [thumbnail] │ │ [thumbnail] │ │ [thumbnail] │                 │
│  │             │ │             │ │             │                 │
│  │ Chú Béo     │ │ Best      │ │ Tasty VN    │                 │
│  │ 1.2M subs   │ │ 500K subs  │ │ 250K subs   │                 │
│  │ 200 videos  │ │ 150 videos │ │ 100 videos  │                 │
│  │ ✅ Ready    │ │ ⏳ Anal.   │ │ ❌ Failed   │                 │
│  │ 3 scripts   │ │ 0 scripts  │ │ 0 scripts   │                 │
│  └─────────────┘ └─────────────┘ └─────────────┘                 │
│                                                                   │
│  [+ Tạo Channel Assistant mới]                                   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### /assistants/[id]

```
┌──────────────────────────────────────────────────────────────────┐
│  ← Back   Chú Béo Channel                               [DELETE] │
├──────────────────────────────────────────────────────────────────┤
│  [CHANNEL THUMBNAIL]   Channel: @chubeo_official                 │
│                        Subscribers: 1,234,567                     │
│                        Videos: 200 collected (50 viral)           │
│                        Status: ✅ Ready                           │
│                                                                   │
│  ACTIONS:                                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────┐ │
│  │ 🧠 Analyze  │ │ 💡 Generate  │ │ ✍️ Generate  │ │ 📊      │ │
│  │ Deep (50c) │ │ Ideas (5c)   │ │ Script(30c)  │ │ History │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └─────────┘ │
│                                                                   │
│  Recent Jobs:                                                     │
│  - 2026-08-05 14:23  script_generate  ✅ done                    │
│  - 2026-08-04 10:15  deep_analysis    ✅ done                    │
│  - 2026-08-03 16:42  collect_channel  ✅ done                    │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. Files to Create

| File | Purpose |
|------|---------|
| `apps/web/app/assistants/page.tsx` | Assistants list page |
| `apps/web/app/assistants/[id]/page.tsx` | Assistant detail page |
| `apps/web/app/api/assistants/route.ts` | GET list |
| `apps/web/app/api/assistants/[id]/route.ts` | GET single + DELETE |
| `apps/web/components/assistant-card.tsx` | Card component |
| `apps/web/components/assistant-actions.tsx` | Action buttons |

---

## 6. Acceptance Summary

| # | Criteria |
|---|----------|
| AC1 | `/assistants` renders list |
| AC2 | Empty state khi không có assistant |
| AC3 | Card shows thumbnail + stats + status |
| AC4 | Click card → detail page |
| AC5 | Detail page shows 4 action buttons |
| AC6 | Action buttons link to right routes |
| AC7 | Delete assistant with confirmation |
| AC8 | API proxy enforces JWT + BFF |
| AC9 | RLS isolation works (user A không thấy user B) |
| AC10 | Responsive mobile |