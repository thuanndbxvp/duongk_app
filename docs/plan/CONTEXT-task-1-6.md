# Bối cảnh Hệ thống (CONTEXT): Task 1.6 - OpenAPI Spec & API Documentation

## 1. Tri thức Tổng hợp
- **Task:** Sprint 1 - Task 1.6: OpenAPI Spec Generation
- **Mục tiêu:** Generate OpenAPI spec tự động và tạo documentation cho frontend team
- **Tài liệu tham khảo:**
  - `docs/plan/PLAN-task-1-6.md` - Kiến trúc chi tiết
  - `docs/implementation_plan_v1_fixes.md` §1.9

## 2. Các File liên quan và Vai trò

| File | Vai trò | Priority |
|------|---------|----------|
| `apps/api/main.py` | Cần update OpenAPI schema | HIGH |
| `apps/api/openapi.py` | Custom OpenAPI info (NEW) | HIGH |
| `scripts/export_openapi.py` | Export schema script (NEW) | MEDIUM |
| `docs/openapi_schema.json` | Generated schema (OUTPUT) | HIGH |
| `docs/schemas.json` | TypeScript schemas (OUTPUT) | HIGH |

## 3. Kiến trúc OpenAPI Generation

```
┌─────────────────────────────────────────────────────────────────┐
│                   OPENAPI SPEC GENERATION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FastAPI App                                                    │
│      │                                                          │
│      ▼                                                          │
│  get_openapi() ──► OpenAPI Schema (JSON)                       │
│      │                                                          │
│      ├──► /openapi.json ──► Full spec for validation            │
│      │                                                          │
│      ├──► /docs ──► Swagger UI                                   │
│      │                                                          │
│      └──► /redoc ──► ReDoc UI                                   │
│                                                                 │
│  Script: export_openapi.py                                      │
│      │                                                          │
│      ├──► schemas.json ──► For TypeScript frontend              │
│      │                                                          │
│      └──► openapi_schema.json ──► Full spec archive             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 4. Ràng buộc (Constraints)

| Ràng buộc | Mô tả |
|-----------|--------|
| **FastAPI** | ≥ 0.100.0 |
| **Schema** | OpenAPI 3.0+ |
| **Docstrings** | All routes cần có docstring |
| **Response Models** | Pydantic models for all responses |
| **Tags** | Đặt tag theo module |

## 5. API Endpoints Documentation Structure

```
Tags:
├── Module 1 - Niche Validate
│   ├── POST /api/research/validate
│   └── GET /api/research/health
│
├── Module 2A - Deep Collection
│   ├── POST /api/collect/channel
│   └── GET /api/collect/health
│
├── Transcript Engine
│   ├── POST /api/transcript/
│   └── GET /api/transcript/health
│
└── Documentation
    ├── GET /openapi.json
    └── GET /docs
```

## 6. Sample OpenAPI Response

```json
{
  "openapi": "3.0.2",
  "info": {
    "title": "YouTube AI SaaS API",
    "version": "1.0.0",
    "description": "Backend API for YouTube Content Intelligence"
  },
  "paths": {
    "/api/research/validate": {
      "post": {
        "tags": ["Module 1 - Niche Validate"],
        "summary": "Validate niche viability",
        "requestBody": { ... },
        "responses": {
          "200": {
            "description": "Validation successful",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/NicheValidationResponse" }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "NicheValidationResponse": { ... }
    }
  }
}
```
