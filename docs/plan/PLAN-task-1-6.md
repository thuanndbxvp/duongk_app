# Kiến trúc & Luồng xử lý (PLAN): Task 1.6 - OpenAPI Spec & API Documentation

## 1. Mục tiêu

- Generate OpenAPI spec tự động từ FastAPI routes
- Tạo tài liệu API đầy đủ cho frontend team
- Hỗ trợ Schema synchronization giữa Backend và Frontend

## 2. Các bước thực hiện

### 2.1. OpenAPI Spec Generation

Thêm endpoint trong FastAPI để expose OpenAPI spec:

```python
# apps/api/main.py
from fastapi.openapi.utils import get_openapi

app = FastAPI(...)

@app.get("/openapi.json", tags=["Documentation"])
async def openapi():
    """Return OpenAPI specification as JSON."""
    return get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
        description="YouTube AI SaaS API - Backend for Content Intelligence"
    )

@app.get("/docs", tags=["Documentation"])
async def docs_redirect():
    """Redirect to Swagger UI."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/redoc")
```

### 2.2. Custom OpenAPI Info

```python
# apps/api/openapi.py
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="YouTube AI SaaS API",
        version="1.0.0",
        description="""
        ## API Overview
        
        This API provides YouTube content intelligence capabilities:
        
        ### Modules
        - **Module 1**: Niche Validation (Discovery)
        - **Module 2A**: Deep Collection (Metadata + Transcripts)
        - **Module 3**: AI Script Generation
        
        ### Authentication
        All endpoints require JWT Bearer token (except `/health`).
        
        ### Rate Limits
        - Anonymous: 10 requests/minute
        - Authenticated: 100 requests/minute
        
        ### Errors
        See [Error Codes](#section/Errors) for details.
        """,
        routes=app.routes,
    )
    
    # Add custom info
    openapi_schema["info"]["contact"] = {
        "name": "API Support",
        "email": "api@appdk.vn"
    }
    openapi_schema["info"]["license"] = {
        "name": "Proprietary"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### 2.3. API Routes Documentation

Đảm bảo tất cả routes có docstrings:

```python
@app.post(
    "/api/research/validate",
    tags=["Module 1 - Niche Validate"],
    summary="Validate niche viability",
    response_model=NicheValidationResponse,
    responses={
        200: {"description": "Validation successful"},
        400: {"description": "Invalid keyword"},
        429: {"description": "Rate limited"},
        500: {"description": "Internal server error"},
    }
)
async def validate_niche(
    keyword: str = Body(..., description="Keyword to validate"),
    user_id: str = Body("system", description="User ID for testing")
):
    """
    Validate if a niche is viable for YouTube content creation.
    
    - Checks Google Trends data
    - Analyzes competitor landscape
    - Estimates potential views
    
    **Note:** This endpoint uses Redis caching. Subsequent calls
    for the same keyword return cached results.
    """
    pass
```

### 2.4. Schema Synchronization

Tạo script để export schemas cho frontend:

```bash
# scripts/export_openapi.py
import json
import httpx
import asyncio

async def export_schemas():
    """Export OpenAPI schema for frontend team."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/openapi.json")
        schema = response.json()
        
        # Save full schema
        with open("openapi_schema.json", "w") as f:
            json.dump(schema, f, indent=2)
        
        # Extract only schemas
        schemas = {"components": {"schemas": schema.get("components", {}).get("schemas", {})}}
        with open("schemas.json", "w") as f:
            json.dump(schemas, f, indent=2)
        
        print("Exported schemas to schemas.json")

if __name__ == "__main__":
    asyncio.run(export_schemas())
```

## 3. Output Deliverables

| File | Mô tả |
|------|--------|
| `/openapi.json` | Full OpenAPI spec (auto-generated) |
| `/schemas.json` | Only schemas for TypeScript generation |
| `/docs` | Swagger UI |
| `/redoc` | ReDoc UI |

## 4. Verification

- [ ] `GET /openapi.json` trả về valid JSON schema
- [ ] Swagger UI hiển thị đầy đủ endpoints
- [ ] All response models có JSON schema
- [ ] `scripts/export_openapi.py` chạy thành công

## 5. Dependencies

- `fastapi>=0.115.0`
- `httpx` (for export script)

## 6. Ghi chú

- OpenAPI spec được generate tự động từ type hints
- Không cần viết tay schema — chỉ cần định nghĩa Pydantic models
