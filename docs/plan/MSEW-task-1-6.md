# MSEW: Task 1.6 - OpenAPI Spec & API Documentation

> **Prerequisites:**
> - **Repomix bundle:** `.\CONTEXT_BUNDLE.md`
> - **Python venv activated:** `.\venv\Scripts\Activate.ps1`
> - **Dependencies:** `pip install httpx`
> - **API running:** `uvicorn apps.api.main:app --reload`

---

## Skill Routing Summary

| Step | Tiêu đề Step | Primary Skill | Reference Skill | Fallback Skill |
|------|--------------|---------------|-----------------|----------------|
| 1 | OpenAPI Custom Schema | `backend-development` | `general-purpose` | - |
| 2 | Update main.py | `backend-development` | - | - |
| 3 | Export Script | `general-purpose` | - | - |
| 4 | Add Route Docstrings | `backend-development` | - | - |
| 5 | Verify Generation | `tester` | - | - |

---

## Files KHÔNG được đụng (Do Not Touch)
- `apps/api/modules/*/service.py` — Business logic
- `apps/api/modules/*/schemas.py` — Pydantic models
- `apps/worker/` — Worker code

---

## Micro-Steps

### Step 1: Tạo Custom OpenAPI Schema Module

**File:** `apps/api/openapi.py`
**Vị trí:** Tạo file mới

**Code cần viết:**
```python
"""
Custom OpenAPI Schema Configuration.

Adds metadata, tags, and custom info to auto-generated OpenAPI spec.
"""
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi_schema(app: FastAPI) -> dict:
    """
    Generate custom OpenAPI schema with additional metadata.
    
    Args:
        app: FastAPI application instance
    
    Returns:
        OpenAPI schema dictionary
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="YouTube AI SaaS API",
        version="1.0.0",
        description="""
## API Overview

This API provides YouTube content intelligence capabilities for automated video content creation.

### Modules

- **Module 1 - Niche Validate**: Validates YouTube niche viability using Google Trends
- **Module 2A - Deep Collection**: Collects video metadata from YouTube channels
- **Transcript Engine**: 3-tier transcript retrieval (YouTube API → Supadata → Whisper)

### Authentication

All endpoints require JWT Bearer token in the Authorization header (except `/health`).

### Rate Limits

- Anonymous: 10 requests/minute
- Authenticated: 100 requests/minute

### Errors

All errors return standard JSON format:

```json
{
  "detail": "Error message description"
}
```

### Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Internal Server Error |
""",
        routes=app.routes,
    )
    
    # Add custom info
    openapi_schema["info"]["contact"] = {
        "name": "API Support",
        "email": "api@appdk.vn",
        "url": "https://appdk.vn"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "Proprietary",
        "url": "https://appdk.vn/terms"
    }
    
    # Add servers
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Local Development"
        },
        {
            "url": "https://api.staging.appdk.vn",
            "description": "Staging"
        },
        {
            "url": "https://api.appdk.vn",
            "description": "Production"
        }
    ]
    
    # Add tags metadata
    openapi_schema["tags"] = [
        {
            "name": "Module 1 - Niche Validate",
            "description": "Validates YouTube niche viability"
        },
        {
            "name": "Module 2A - Deep Collection",
            "description": "Collects video metadata from YouTube channels"
        },
        {
            "name": "Transcript Engine",
            "description": "3-tier transcript retrieval"
        },
        {
            "name": "Documentation",
            "description": "API documentation endpoints"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema
```

**Verify command (PowerShell):**
```powershell
python -c "from apps.api.openapi import custom_openapi_schema; print('OK')"
```

**Expected output:**
```
OK
```

---

### Step 2: Update apps/api/main.py

**File:** `apps/api/main.py`
**Vị trí:** Sau imports, trước `app = FastAPI(...)`

**Import cần thêm:**
```python
# OpenAPI custom schema
from apps.api.openapi import custom_openapi_schema
```

**Và sau `app = FastAPI(...)`:**

**Tìm dòng:**
```python
app = FastAPI(...)
```

**Thêm sau đó:**
```python
# Set custom OpenAPI schema
app.openapi = lambda: custom_openapi_schema(app)
```

**Hoặc thêm vào cuối file (sau tất cả routes):**

```python
# Override default OpenAPI schema
app.openapi = lambda: custom_openapi_schema(app)
```

---

### Step 3: Thêm Documentation Endpoints

**File:** `apps/api/main.py`
**Vị trí:** Trong `apps/api/main.py`, thêm routes sau imports

**Import cần thêm:**
```python
from fastapi.responses import RedirectResponse
```

**Code cần thêm (sau app initialization):**

```python
@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API docs."""
    return RedirectResponse(url="/docs")


@app.get("/openapi.json", include_in_schema=False)
async def openapi_json():
    """Return raw OpenAPI spec as JSON."""
    return app.openapi()


@app.get("/redoc", include_in_schema=False)
async def redoc():
    """Redirect to ReDoc documentation."""
    return RedirectResponse(url="/docs")
```

---

### Step 4: Tạo Export Script

**File:** `scripts/export_openapi.py`
**Vị trí:** Tạo file mới

**Code cần viết:**
```python
#!/usr/bin/env python
"""
Export OpenAPI Schema for Frontend Team.

This script fetches the OpenAPI schema from the running API
and exports it to JSON files for TypeScript generation.
"""
import json
import asyncio
from pathlib import Path
import httpx


API_BASE_URL = "http://localhost:8000"
OUTPUT_DIR = Path("docs")


async def export_schemas():
    """Export OpenAPI schema to JSON files."""
    
    print(f"Fetching OpenAPI schema from {API_BASE_URL}/openapi.json...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch full OpenAPI schema
        response = await client.get(f"{API_BASE_URL}/openapi.json")
        response.raise_for_status()
        full_schema = response.json()
        
        # Ensure output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save full schema
        full_schema_path = OUTPUT_DIR / "openapi_schema.json"
        with open(full_schema_path, "w", encoding="utf-8") as f:
            json.dump(full_schema, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved full schema to {full_schema_path}")
        
        # Extract only schemas (for TypeScript generation)
        schemas = {
            "components": {
                "schemas": full_schema.get("components", {}).get("schemas", {})
            },
            "info": full_schema.get("info", {}),
            "openapi": full_schema.get("openapi", "")
        }
        
        schemas_path = OUTPUT_DIR / "schemas.json"
        with open(schemas_path, "w", encoding="utf-8") as f:
            json.dump(schemas, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved schemas to {schemas_path}")
        
        # Generate TypeScript types (basic)
        ts_types = _generate_typescript_types(schemas["components"]["schemas"])
        ts_types_path = OUTPUT_DIR / "api-types.ts"
        with open(ts_types_path, "w", encoding="utf-8") as f:
            f.write(ts_types)
        print(f"✓ Saved TypeScript types to {ts_types_path}")
        
        # Summary
        schema_count = len(schemas["components"]["schemas"])
        print(f"\n✅ Export complete!")
        print(f"   - {schema_count} schemas exported")
        print(f"   - Output directory: {OUTPUT_DIR.absolute()}")


def _generate_typescript_types(schemas: dict) -> str:
    """Generate TypeScript types from OpenAPI schemas."""
    lines = [
        "// Auto-generated from OpenAPI schema",
        "// Do not edit manually",
        "",
        "export interface OpenAPISchema {",
    ]
    
    for name, schema in schemas.items():
        lines.append(f"  // Schema: {name}")
        
        # Handle basic types
        if "type" in schema:
            if schema["type"] == "object" and "properties" in schema:
                lines.append(f"  export interface {name} {{")
                for prop_name, prop in schema["properties"].items():
                    prop_type = _map_openapi_to_ts(prop)
                    required = prop_name in schema.get("required", [])
                    lines.append(f"    {prop_name}{'' if required else '?'}: {prop_type};")
                lines.append("  }")
            elif schema["type"] == "array" and "items" in schema:
                item_type = _map_openapi_to_ts(schema["items"])
                lines.append(f"  export type {name} = {item_type}[];")
            else:
                lines.append(f"  export type {name} = {_map_openapi_to_ts(schema)};")
        
        lines.append("")
    
    lines.append("}")
    return "\n".join(lines)


def _map_openapi_to_ts(schema: dict) -> str:
    """Map OpenAPI type to TypeScript type."""
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]
    
    openapi_type = schema.get("type", "string")
    
    type_mapping = {
        "string": "string",
        "integer": "number",
        "number": "number",
        "boolean": "boolean",
        "array": "unknown[]",
        "object": "Record<string, unknown>",
        "null": "null"
    }
    
    return type_mapping.get(openapi_type, "unknown")


if __name__ == "__main__":
    asyncio.run(export_schemas())
```

**Verify command (PowerShell):**
```powershell
python scripts/export_openapi.py
```

**Expected output:**
```
Fetching OpenAPI schema from http://localhost:8000/openapi.json...
✓ Saved full schema to docs\openapi_schema.json
✓ Saved schemas to docs\schemas.json
✓ Saved TypeScript types to docs\api-types.ts

✅ Export complete!
   - 15 schemas exported
   - Output directory: d:\appDK\docs
```

---

### Step 5: Verify OpenAPI Generation

**Bước 5a: Start API (nếu chưa chạy)**
```powershell
.\venv\Scripts\Activate.ps1
uvicorn apps.api.main:app --reload --port 8000
```

**Bước 5b: Test OpenAPI endpoint**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/openapi.json" -Method Get | ConvertFrom-Json | Select-Object -ExpandProperty info
```

**Expected output:**
```
title                                      version
-----                                      -------
YouTube AI SaaS API                        1.0.0
```

**Bước 5c: Verify Swagger UI**
```powershell
Start-Process "http://localhost:8000/docs"
```

**Expected:** Browser opens with Swagger UI showing all endpoints

**Bước 5d: Verify ReDoc**
```powershell
Start-Process "http://localhost:8000/redoc"
```

**Expected:** Browser opens with ReDoc showing API documentation

**Bước 5e: Run export script**
```powershell
python scripts/export_openapi.py
```

**Expected:**
```
✓ Saved full schema to docs\openapi_schema.json
✓ Saved schemas to docs\schemas.json
✓ Saved TypeScript types to docs\api-types.ts
```

**Bước 5f: Verify exported files**
```powershell
Get-ChildItem docs/*.json, docs/*.ts | Select-Object Name, Length
```

**Expected:**
```
Name                                      Length
----                                      ------
api-types.ts                              1234
openapi_schema.json                       5678
schemas.json                              2345
```

---

### Step 6: Update Route Docstrings (Optional Enhancement)

Kiểm tra tất cả routes trong `apps/api/modules/*/routes.py` đã có docstrings:

```python
# Ví dụ:
@router.post("/validate", response_model=NicheValidationResponse)
async def validate_niche(request: NicheValidationRequest):
    """
    Validate niche viability for YouTube content creation.
    
    - Checks Google Trends data
    - Analyzes competitor landscape
    - Estimates potential views
    
    **Note:** This endpoint uses Redis caching. Subsequent calls
    for the same keyword return cached results.
    """
```

Nếu thiếu docstring, bổ sung theo format trên.

---

**Verify command (PowerShell):**
```powershell
# Check if all routes have docstrings
$routes = @(
    "apps/api/modules/module_1/routes.py",
    "apps/api/modules/module_2a/routes.py",
    "apps/api/modules/transcript/routes.py"
)

foreach ($route in $routes) {
    $content = Get-Content $route -Raw
    if ($content -match '""".*?"""\s*\n\s*async def') {
        Write-Host "✓ $route has docstrings"
    } else {
        Write-Host "✗ $route missing docstrings"
    }
}
```

---

**Nếu fail:** 
- Invoke skill `debugging`.
- Báo cáo vào file `BLOCKERS.md`.
- **CẤM TỰ SỬA CODE KHÁC.**
