# PLAN: Phase 11 — Character/Background Lab

## 1. Mục tiêu
- Bắt buộc tạo character/background anchors TRƯỚC khi batch scene assets.
- Tránh character drift, giảm retry tốn credits.

## 2. Workflow bắt buộc
```text
Scene Plan approved
  → Lab start (cost estimate)
  → Generate candidates per anchor
  → User browse + select + regenerate
  → Coverage check (mọi scene có anchor)
  → User approve
  → Phase 10 batch scene assets
```

## 3. Rủi ro
| Rủi ro | Giảm thiểu |
|---|---|
| Regenerate tốn credits | cap 5/anchor. |
| Provider capability khác nhau | chuẩn hoá binding_strength 0..1, provider tự map. |
| Style bible đổi version phá lab | snapshot bible_version vào lab_run. |
| User approve khi thiếu anchor | API 422 + UI disable. |