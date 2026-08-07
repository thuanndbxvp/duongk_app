# Phase 2 — Wire Existing Components

> **Goal**: Connect 3 existing tabs to backend API + add script regeneration flow.
> **Effort**: 3 ngày
> **Risk**: LOW (reuse existing assets)
> **Prerequisite**: P1 (drift fixes confirmed)
> **Source**: `docs/HIDDEN-FEATURES-GAP-ANALYSIS.md` §3.1.A (analysis), §3.1.G (scripts)

---

## 1. Vấn đề

Audit phát hiện 8 components đã có UI nhưng KHÔNG gọi API:

| Component | Has UI? | Has API? | Issue |
|---|---|---|---|
| `<AnalysisTabs>` | ✅ | ❌ | Tabs exist, không có data load |
| `<NlpTab>` | ✅ | ✅ `/api/analysis/{id}/nlp` | Props only, không fetch |
| `<LlmTab>` | ✅ | ✅ `/api/analysis/{id}/llm` | Props only |
| `<DeterministicTab>` | ✅ | ✅ `/api/analysis/{id}/deterministic` | Props only |
| `<InsightsTab>` | ✅ | ✅ `/api/analysis/{id}/insights` | Props only |
| `<ThumbnailTab>` | ✅ | ✅ `/api/analysis/{id}/thumbnail` | Props only |
| `<ScriptEditor>` | ✅ | ✅ `/api/scripts/{id}/regenerate` | No regenerate button |
| `<ScriptEditor>` | ✅ | ✅ `/api/scripts/{id}/versions` | No version history |

## 2. Acceptance Criteria

### 2.1 Analysis tabs

- [ ] `<AnalysisPage>` (`app/(dashboard)/analysis/[assistant_id]/page.tsx`) hiện đang gọi `GET /api/analysis/{id}` (returns full payload)
- [ ] Refactor: thay vì 1 call, gọi 4 sub-endpoints:
  - `GET /api/analysis/{id}/nlp` (sentiment, entities, keywords)
  - `GET /api/analysis/{id}/llm` (LLM-generated insights)
  - `GET /api/analysis/{id}/deterministic` (rule-based metrics)
  - `GET /api/analysis/{id}/output` (full output JSON)
- [ ] Mỗi tab fetch data riêng (parallel với `Promise.all` ở server component)
- [ ] Loading state per tab (skeleton)
- [ ] Error state per tab (retry button)
- [ ] Tab badges: hiển thị số lượng items (e.g., "NLP (12)")

### 2.2 Script regenerate

- [ ] Component `<ScriptEditor>`: thêm button "Regenerate" góc trên-phải
- [ ] Click → mở `<RegenerateDialog>` với textarea nhập feedback
- [ ] Submit → call `POST /api/scripts/{id}/regenerate` với body `{feedback: "..."}`
- [ ] Loading state + disable button
- [ ] Success → refresh page + show toast "Script regenerated"
- [ ] Error → show alert with backend error message

### 2.3 Script versions

- [ ] Component `<ScriptEditor>`: thêm dropdown "v{N}" ở header
- [ ] Dropdown list từ `GET /api/scripts/{id}/versions`
- [ ] Select version → load script content từ version payload
- [ ] "Compare" button: show diff giữa current và selected version
- [ ] Save → update current version

### 2.4 Tests

- [ ] Unit test: `<AnalysisTabs>` renders 4 tabs với data
- [ ] Unit test: `<ScriptEditor>` regenerate flow
- [ ] Integration test: 4 analysis endpoints return data
- [ ] Integration test: script regenerate endpoint creates new version

## 3. Implementation Outline

### 3.1 New server component helper

**File: `apps/web/lib/analysis-client.ts` (MỚI)**

```typescript
import { apiFetch } from "@/lib/api-client";

export interface AnalysisOutput {
  nlp: NLPSection;
  llm: LLMSection;
  deterministic: DeterministicSection;
  insights: InsightsSection;
  thumbnail: ThumbnailSection;
  output: FullOutput;
}

export async function fetchAnalysisFull(assistantId: string, token: string) {
  const [nlp, llm, deterministic, insights, thumbnail, output] = await Promise.all([
    apiFetch(`/api/analysis/${assistantId}/nlp`, { cache: "no-store" }, token),
    apiFetch(`/api/analysis/${assistantId}/llm`, { cache: "no-store" }, token),
    apiFetch(`/api/analysis/${assistantId}/deterministic`, { cache: "no-store" }, token),
    apiFetch(`/api/analysis/${assistantId}/insights`, { cache: "no-store" }, token),
    apiFetch(`/api/analysis/${assistantId}/thumbnail`, { cache: "no-store" }, token),
    apiFetch(`/api/analysis/${assistantId}/output`, { cache: "no-store" }, token),
  ]);
  return { nlp, llm, deterministic, insights, thumbnail, output };
}
```

### 3.2 Refactor AnalysisPage

**File: `apps/web/app/(dashboard)/analysis/[assistant_id]/page.tsx` (SỬA)**

```tsx
// Before:
const r = await apiFetch(`/api/analysis/${id}`, { cache: "no-store" }, token);
const data = await r.json();
return <AnalysisTabs data={data} />;

// After:
const { nlp, llm, deterministic, insights, thumbnail, output } = await fetchAnalysisFull(id, token);
return (
  <AnalysisTabs
    nlp={nlp}
    llm={llm}
    deterministic={deterministic}
    insights={insights}
    thumbnail={thumbnail}
    output={output}
  />
);
```

### 3.3 Update AnalysisTabs

**File: `apps/web/components/analysis/analysis-tabs.tsx` (SỬA)**

```tsx
interface Props {
  nlp: NLPSection;
  llm: LLMSection;
  deterministic: DeterministicSection;
  insights: InsightsSection;
  thumbnail: ThumbnailSection;
  output: FullOutput;
}

export function AnalysisTabs({ nlp, llm, deterministic, insights, thumbnail, output }: Props) {
  return (
    <Tabs defaultValue="nlp">
      <TabsList>
        <TabsTrigger value="nlp">NLP ({nlp.entities?.length || 0})</TabsTrigger>
        <TabsTrigger value="llm">LLM ({llm.insights?.length || 0})</TabsTrigger>
        <TabsTrigger value="deterministic">Metrics ({deterministic.metrics?.length || 0})</TabsTrigger>
        <TabsTrigger value="insights">Insights ({insights.count || 0})</TabsTrigger>
        <TabsTrigger value="thumbnail">Thumbnails ({thumbnail.candidates?.length || 0})</TabsTrigger>
      </TabsList>
      <TabsContent value="nlp"><NlpTab data={nlp} /></TabsContent>
      <TabsContent value="llm"><LlmTab data={llm} /></TabsContent>
      <TabsContent value="deterministic"><DeterministicTab data={deterministic} /></TabsContent>
      <TabsContent value="insights"><InsightsTab data={insights} /></TabsContent>
      <TabsContent value="thumbnail"><ThumbnailTab data={thumbnail} /></TabsContent>
    </Tabs>
  );
}
```

### 3.4 Script regenerate dialog

**File: `apps/web/components/script-regenerate-dialog.tsx` (MỚI)**

```tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

interface Props {
  scriptId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function ScriptRegenerateDialog({ scriptId, isOpen, onClose }: Props) {
  const router = useRouter();
  const [feedback, setFeedback] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async () => {
    if (!feedback.trim()) return alert("Vui lòng nhập feedback");
    setIsLoading(true);
    try {
      const r = await fetch(`/api/scripts/${scriptId}/regenerate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feedback }),
      });
      if (!r.ok) throw new Error(`Regenerate failed: ${await r.text()}`);
      router.refresh();
      onClose();
    } catch (e) {
      alert("Lỗi: " + (e as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Regenerate Script</DialogTitle>
        </DialogHeader>
        <div>
          <label>Feedback (muốn thay đổi gì?)</label>
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="VD: 'Thêm chi tiết về nhân vật chính'"
            rows={4}
            className="w-full"
          />
        </div>
        <DialogFooter>
          <button onClick={onClose} disabled={isLoading}>Hủy</button>
          <button onClick={handleSubmit} disabled={isLoading}>
            {isLoading ? "Đang generate..." : "Regenerate"}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

### 3.5 Script versions dropdown

**File: `apps/web/components/script-version-dropdown.tsx` (MỚI)**

```tsx
"use client";
import { useState, useEffect } from "react";

interface Props {
  scriptId: string;
  currentVersion: number;
  onVersionChange: (version: number) => void;
}

export function ScriptVersionDropdown({ scriptId, currentVersion, onVersionChange }: Props) {
  const [versions, setVersions] = useState<{ version: number; created_at: string }[]>([]);

  useEffect(() => {
    fetch(`/api/scripts/${scriptId}/versions`)
      .then((r) => r.json())
      .then((data) => setVersions(data.versions || []));
  }, [scriptId]);

  return (
    <select
      value={currentVersion}
      onChange={(e) => onVersionChange(Number(e.target.value))}
      className="border px-2 py-1 rounded"
    >
      {versions.map((v) => (
        <option key={v.version} value={v.version}>
          v{v.version} ({new Date(v.created_at).toLocaleDateString()})
        </option>
      ))}
    </select>
  );
}
```

## 4. Files thay đổi

| File | Action | LOC |
|---|---|---|
| `apps/web/lib/analysis-client.ts` | MỚI | +30 |
| `apps/web/app/(dashboard)/analysis/[assistant_id]/page.tsx` | SỬA | +15 |
| `apps/web/components/analysis/analysis-tabs.tsx` | SỬA | +30 |
| `apps/web/components/script-regenerate-dialog.tsx` | MỚI | +60 |
| `apps/web/components/script-version-dropdown.tsx` | MỚI | +40 |
| `apps/web/components/script-editor.tsx` | SỬA | +10 |
| `tests/web/components/test_script_regenerate.tsx` | MỚI | +50 |
| `tests/web/components/test_analysis_tabs.tsx` | MỚI | +40 |

## 5. Test plan

```bash
# Unit tests
pytest tests/web/components/test_script_regenerate.tsx -v
pytest tests/web/components/test_analysis_tabs.tsx -v

# Integration tests
pytest tests/api/test_analysis_subendpoints.py -v
pytest tests/api/test_script_regenerate.py -v

# E2E
bash scripts/run_e2e_local.sh
```

## 6. Done when

- [ ] 4 analysis sub-endpoints called từ AnalysisPage
- [ ] 5 tabs render với data từ server
- [ ] Script regenerate + versions flow works
- [ ] Tests pass
- [ ] No new dependencies
- [ ] LoC delta: +250 / -20
- [ ] Tier 1 sign-off
