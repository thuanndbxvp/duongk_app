# Phase 4 — Context & Background

## 1. Why this phase exists

Style Bible là **visual style guide** cho project. Nó define:
- Colors (palette chính)
- Typography (font chữ)
- Characters (nhân vật recurring)
- Backgrounds (background recurring)

Mục đích: **Consistency** giữa các scenes trong cùng series video. Khi user sinh scene 5, hệ thống auto-apply style bible → character giống nhân vật series, color palette consistent.

## 2. Background: Section types

Backend cho phép 4 section types:
- **color**: `{hex: string, name: string}`
- **typography**: `{font: string, weight: string, size: string}`
- **character**: `{name: string, image_url: string, description: string}`
- **background**: `{name: string, image_url: string, description: string}`

Mỗi section là một JSON object trong DB.

## 3. Background: Preview generation

POST /api/style-bibles/{id}/preview:
1. Backend compose image từ all sections
2. Output: PNG file với color palette + typography sample + character images
3. Returns URL để user download

## 4. Background: Apply to project

Apply to project feature chưa có backend logic đầy đủ. Tier 2 chỉ làm UI button "Apply to project" với stub.

## 5. What is NOT in this phase

- Bulk character variants
- Style bible import/export
- Auto-extract style from image (AI)
- Sharing với team members

## 6. References

- `apps/api/modules/style_bible/routes.py` (existing endpoints)
- `docs/HIDDEN-FEATURES-GAP-ANALYSIS.md` §3.1.C