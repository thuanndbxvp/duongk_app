# Phân bổ Kỹ năng (SKILL-ROUTING): Task 1.6 - OpenAPI Spec & API Documentation

## 1. Chiến lược tổng thể (Overall Strategy)

Task 1.6 tập trung vào:
- FastAPI OpenAPI configuration
- Documentation generation
- Schema export automation

Đây là task backend nhẹ, chủ yếu là configuration và script.

## 2. Bảng Phân bổ theo Step (Per-step Mapping)

| MSEW Step | Task ID / Tên | Primary Skill | Reference Skill | Fallback Skill | Lý do định tuyến |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Step 1 | OpenAPI Custom Schema | `backend-development` | `general-purpose` | - | FastAPI configuration |
| Step 2 | Update main.py | `backend-development` | - | - | Add OpenAPI endpoints |
| Step 3 | Export Script | `general-purpose` | - | - | Python script |
| Step 4 | Add Route Docstrings | `backend-development` | - | - | Documentation |
| Step 5 | Verify Generation | `tester` | - | - | Testing |

## 3. Các kỹ năng xuyên suốt (Cross-cutting Skills)

| Skill | Khi nào gọi | Mục đích |
|-------|--------------|----------|
| `general-purpose` | Script writing | Export script |
| `backend-development` | FastAPI config | OpenAPI setup |
| `tester` | Verification | Test endpoints |

## 4. Files KHÔNG được đụng (Do Not Touch)

| File | Lý do |
|------|-------|
| `apps/api/modules/*/service.py` | Business logic đã code |
| `apps/api/modules/*/schemas.py` | Pydantic models đã defined |
| `apps/worker/` | Worker code thuộc task khác |

## 5. Special Considerations

### FastAPI OpenAPI
- FastAPI tự generate OpenAPI từ type hints
- Cần custom `openapi_schema` để thêm metadata
- Tags phải khớp với router prefixes

### Schema Export
- `httpx` để call local API
- Chạy sau khi `uvicorn` started
- Output ra JSON files cho frontend

## 6. Verification Strategy

| Step | Verify Command | Expected |
|------|----------------|----------|
| 1-2 | `http://localhost:8000/openapi.json` | Valid JSON |
| 1-2 | `http://localhost:8000/docs` | Swagger UI loads |
| 3 | `python scripts/export_openapi.py` | Files created |
| 4 | Manual review | All routes documented |
| 5 | `http://localhost:8000/redoc` | ReDoc UI loads |
