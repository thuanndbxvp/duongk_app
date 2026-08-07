# Phase 2 — Context & Background

## 1. Why this phase exists

Tier 1 audit phát hiện 8 components đã render UI nhưng KHÔNG gọi API. Đây là "rendered but not functional" — user click vào tabs hoặc button nhưng không thấy data.

3 components quan trọng nhất:
- `<AnalysisTabs>` — 5 tabs, zero data
- `<ScriptEditor>` — không có regenerate button
- `<ScriptEditor>` — không có version history

## 2. Background: Analysis sub-modules

Backend đã implement 6 sub-endpoints cho `/api/analysis/{id}/...`:
- `/nlp` — sentiment, entities, keywords
- `/llm` — LLM-generated insights
- `/deterministic` — rule-based metrics
- `/insights` — insight items
- `/thumbnail` — thumbnail candidates
- `/output` — full output JSON

Trước đây, frontend gọi 1 endpoint `/api/analysis/{id}` trả về payload combined. Sau refactor, mỗi tab fetch 1 endpoint riêng → lazy loading, faster initial render.

## 3. Background: Script regeneration

User flow mong muốn:
1. User generate script từ idea
2. Đọc script → không thích phần kết
3. Click "Regenerate" → nhập "thêm chi tiết về nhân vật chính"
4. Backend generate version mới với feedback
5. User compare version 1 vs 2 → chọn version 2

Hiện tại flow này KHÔNG tồn tại trong UI. Backend đã support từ Phase 3 (script versions table).

## 4. Background: Script versions

DB table `scripts` có column `version` (int). Backend tạo snapshot mỗi khi regenerate. Endpoint `GET /api/scripts/{id}/versions` returns list versions.

Frontend cần:
- Dropdown để chọn version
- Diff visualization
- Compare current vs selected

## 5. What is NOT in this phase

- Style Bible UI (P4)
- Voice Profiles (P3)
- Asset Library (P5)
- Channel Collector (P5)

Tier 2 chỉ focus 3 features trên. Đừng over-engineer.

## 6. References

- `docs/HIDDEN-FEATURES-GAP-ANALYSIS.md` §3.1.A, §3.1.G
- `apps/api/modules/analysis/routes.py` (6 sub-endpoints)
- `apps/api/modules/scripts/routes.py` (regenerate + versions)
- `apps/web/components/analysis/*` (existing tabs)
