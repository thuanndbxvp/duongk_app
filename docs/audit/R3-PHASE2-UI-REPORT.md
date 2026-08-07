# R3-PHASE2-UI-REPORT: Surfacing the Hidden Gems

> **Auditor**: Tier 1 (Principal System Architect)
> **Subject**: Phase 2 UI Implementation
> **Date**: 2026-08-07
> **Reference**: ROUND-3-AUDIT.md

---

## TÓM TẮT ĐIỀU HÀNH

| Page | Route | Status | Features |
|---|---|---|---|
| Admin Usage | `/admin/usage` | ✅ HOÀN THÀNH | Stats, filters, pagination, real-time logs |
| Cost Estimator | `/admin/routing/estimate` | ✅ HOÀN THÀNH | Feature selection, token inputs, provider breakdown |
| Render Config Editor | `/projects/[id]/render-config` | ✅ HOÀN THÀNH | Zod schema, react-hook-form, full FFmpeg config |
| Timeline Debugger | `/projects/[id]/timeline-debug` | ✅ HOÀN THÀNH | Visual editor, JSON view, drag-drop scenes |

---

## PHẦN 1: ADMIN USAGE PAGE

### Route
```
/admin/usage
```

### File Created
```
apps/web/app/(admin)/admin/usage/page.tsx
```

### Features
- **Stats Cards**: Total calls, cost, tokens, latency, success rate
- **Filters**: Feature, status, date range
- **Table**: Time, user, feature, provider, tokens, cost, latency, status
- **Pagination**: 50 items per page, prev/next navigation
- **Real-time**: Fetches from `api_usage_logs` table

### API Calls
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/admin/analytics/usage-stats` | Fetch aggregate stats |
| GET | `/api/admin/usage-logs` | Fetch paginated logs with filters |

### TypeScript Types
```typescript
interface ApiUsageLog {
  id: string;
  user_id: string;
  feature: string;
  provider: string;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  latency_ms: number;
  status: string;
  created_at: string;
}
```

---

## PHẦN 2: COST ESTIMATOR PAGE

### Route
```
/admin/routing/estimate
```

### File Created
```
apps/web/app/(admin)/admin/routing/estimate/page.tsx
```

### Features
- **Feature Selection**: transcript, llm_text, embedding, tts, thumbnail_vision
- **Token Inputs**: Input tokens, output tokens, number of calls
- **Cost Breakdown**: By provider with percentage bars
- **Provider Reference Table**: Current pricing for all providers
- **Local Calculation**: Falls back to local math if API fails

### API Calls
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/admin/routing-config/{feature}/cost-estimate` | Get real-time estimate |

### Provider Pricing (Hardcoded Defaults)
| Provider | Input $/1K | Output $/1K | Flat Call |
|---|---|---|---|
| OpenAI GPT-4o-mini | $0.00015 | $0.0006 | - |
| Gemini 1.5 Flash | $0.000035 | $0.00016 | - |
| Groq Llama-3 | $0.0001 | $0.0001 | - |
| OmniVoice (Modal) | - | - | $0.05 |
| ElevenLabs | - | - | $0.30 |

---

## PHẦN 3: RENDER CONFIG EDITOR

### Route
```
/projects/[id]/render-config
```

### File Created
```
apps/web/app/(dashboard)/projects/[id]/render-config/page.tsx
```

### Features
- **Zod Schema Validation**: Full type-safe config
- **Sections**: Video Output, Encoding, GPU, Watermark, Subtitles, Audio, Advanced
- **Form Fields**:
  - Resolution (1920x1080, 4K, etc.)
  - Frame rate (24/30/60 fps)
  - Codec (H.264, H.265, VP9, ProRes)
  - CRF (0-51)
  - GPU encoder selection
  - Watermark position/opacity
  - Subtitle styling
  - Audio normalization/denoise

### API Calls
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/projects/{id}` | Fetch project |
| PATCH | `/api/projects/{id}/render-config` | Save render_config JSONB |

### Zod Schema
```typescript
const RENDER_CONFIG_SCHEMA = z.object({
  resolution: z.enum(['1920x1080', '1280x720', '3840x2160', '2560x1440']),
  frame_rate: z.enum(['24', '30', '60']),
  codec: z.enum(['h264', 'h265', 'vp9', 'prores']),
  crf: z.number().min(0).max(51),
  use_gpu: z.boolean(),
  watermark_enabled: z.boolean(),
  subtitles_enabled: z.boolean(),
  // ... full FFmpeg config
});
```

---

## PHẦN 4: TIMELINE DEBUGGER

### Route
```
/projects/[id]/timeline-debug
```

### File Created
```
apps/web/app/(dashboard)/projects/[id]/timeline-debug/page.tsx
```

### Features
- **Stats Bar**: Total duration, scene count, version
- **Visual Editor**:
  - Scene list with reorder (up/down)
  - Timeline bar visualization
  - Scene details panel (voice, visual, transition)
  - Add/delete scenes
- **JSON View**: Direct JSON editing with validation
- **Dual Mode**: Form view ↔ JSON view toggle

### API Calls
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/projects/{id}` | Fetch project |
| GET | `/api/projects/{id}/timeline` | Fetch timeline JSONB |
| PUT | `/api/projects/{id}/timeline` | Replace timeline (JSON mode) |
| PATCH | `/api/projects/{id}/timeline` | Update timeline (form mode) |

### Timeline Model
```typescript
interface TimelineModel {
  version: string;
  project_id: string;
  total_duration_seconds: number;
  scenes: TimelineScene[];
  metadata?: {
    created_at?: string;
    updated_at?: string;
  };
}

interface TimelineScene {
  id: string;
  order: number;
  duration_seconds: number;
  voice_line?: {
    text: string;
    audio_url?: string;
    status?: string;
  };
  visual?: {
    type: 'text' | 'image' | 'video' | 'slideshow';
    content?: string;
    asset_url?: string;
  };
  transition?: string;
}
```

---

## PHẦN 5: NAVIGATION WIRING

### Admin Sidebar
**File**: `apps/web/app/(admin)/layout.tsx`

Added routes:
```typescript
{ href: '/admin/routing/estimate', label: 'Cost Estimator', icon: IconChannels, enabled: true },
{ href: '/admin/usage', label: 'API Usage', icon: IconChannels, enabled: true },
```

### Project Tabs
**File**: `apps/web/app/(dashboard)/projects/[id]/page.tsx`

Added tabs:
```typescript
const TABS = [
  { id: 'brief', label: 'Brief', href: `/projects/${id}` },
  { id: 'render-config', label: 'Render Config', href: `/projects/${id}/render-config` },
  { id: 'timeline', label: 'Timeline Debug', href: `/projects/${id}/timeline-debug` },
];
```

---

## PHẦN 6: FILES SUMMARY

### Files Created
| Path | Purpose |
|---|---|
| `apps/web/app/(admin)/admin/usage/page.tsx` | API Usage Logs |
| `apps/web/app/(admin)/admin/routing/estimate/page.tsx` | Cost Estimator |
| `apps/web/app/(dashboard)/projects/[id]/render-config/page.tsx` | Render Config Editor |
| `apps/web/app/(dashboard)/projects/[id]/timeline-debug/page.tsx` | Timeline Debugger |

### Files Modified
| Path | Changes |
|---|---|
| `apps/web/app/(admin)/layout.tsx` | Added nav items for Usage + Cost Estimator |
| `apps/web/app/(dashboard)/projects/[id]/page.tsx` | Added project tabs |

---

## PHẦN 7: DEPENDENCIES

### Required Packages
```json
{
  "react-hook-form": "^7.x",
  "@hookform/resolvers": "^3.x",
  "zod": "^3.x"
}
```

### Icons Used
- Standard icons from `@/components/icons`
- No new icon components needed

---

## KẾT LUẬN

**Phase 2: Surfacing the Hidden Gems — HOÀN THÀNH**

1. ✅ Admin Usage page với real-time API logs
2. ✅ Cost Estimator với provider pricing
3. ✅ Render Config Editor với Zod validation
4. ✅ Timeline Debugger với visual + JSON editor
5. ✅ Navigation wired for admin + project routes

### Backend Wiring Status
- ✅ `/admin/usage` → `api_usage_logs` table
- ✅ `/admin/routing/estimate` → `service_routing_config`
- ✅ `/projects/[id]/render-config` → `render_jobs.render_config`
- ✅ `/projects/[id]/timeline-debug` → `timelines.model`

---

## CAM KẾT

| Vai trò | Tên | Ngày | Trạng thái |
|---|---|---|---|
| Principal Architect | Tier 1 | 2026-08-07 | ✅ HOÀN THÀNH |
| Frontend Engineer | Tier 1 | 2026-08-07 | ✅ XÁC NHẬN |
| QA | Chờ đợi | ____ | ☐ Testing pending |
