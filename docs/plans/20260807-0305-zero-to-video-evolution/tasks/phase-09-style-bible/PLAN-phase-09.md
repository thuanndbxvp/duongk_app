# PLAN: Phase 09 — Style Bible

## 1. Mục tiêu
- Style Bible là entity độc lập, versioned.
- Character/background references có anchor_strength.
- `build_prompt()` merge bible + scene.
- Reusable giữa nhiều project.

## 2. Rủi ro
| Rủi ro | Giảm thiểu |
|---|---|
| RAG context tràn | Cap chunk + auto-summary. |
| Character drift giữa provider | anchor_strength > 0.6 + provider hỗ trợ ip_adapter. |
| Negative prompt xung đột với channel forbidden_claims | Ưu tiên channel. |
| Bible version rollback phá scene | scene_style_applications giữ cũ. |