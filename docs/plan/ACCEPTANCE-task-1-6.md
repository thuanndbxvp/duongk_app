# Tiêu chí Nghiệm thu (ACCEPTANCE): Task 1.6 - OpenAPI Spec & API Documentation

## 1. Tiêu chuẩn Chức năng (Functional Criteria)

### OpenAPI Schema
- [ ] **Custom OpenAPI Schema** hoạt động:
  - [ ] `apps/api/openapi.py` tồn tại và import được
  - [ ] `custom_openapi_schema()` trả về valid schema
  - [ ] Title, version, description đúng

- [ ] **Documentation Endpoints**:
  - [ ] `GET /openapi.json` trả về JSON schema
  - [ ] `GET /docs` mở Swagger UI
  - [ ] `GET /redoc` mở ReDoc
  - [ ] `GET /` redirect đến `/docs`

### Schema Export
- [ ] **Export Script** hoạt động:
  - [ ] `scripts/export_openapi.py` chạy thành công
  - [ ] `docs/openapi_schema.json` được tạo
  - [ ] `docs/schemas.json` được tạo
  - [ ] `docs/api-types.ts` được tạo

### Route Documentation
- [ ] **All routes have docstrings**:
  - [ ] `POST /api/research/validate`
  - [ ] `GET /api/research/health`
  - [ ] `POST /api/collect/channel`
  - [ ] `GET /api/collect/health`
  - [ ] `POST /api/transcript/`
  - [ ] `GET /api/transcript/health`

### OpenAPI Tags
- [ ] **Tags properly assigned**:
  - [ ] Module 1 routes có tag "Module 1 - Niche Validate"
  - [ ] Module 2A routes có tag "Module 2A - Deep Collection"
  - [ ] Transcript routes có tag "Transcript Engine"

## 2. Tiêu chuẩn Phi chức năng (Non-functional)

| Tiêu chí | Yêu cầu | Verification |
|----------|---------|--------------|
| **OpenAPI Version** | 3.0+ | Check openapi field |
| **Schema Valid** | JSON schema compliant | validator |
| **Documentation** | All endpoints documented | Manual review |
| **TypeScript** | Valid TypeScript syntax | `npx tsc --noEmit` |
| **Performance** | /openapi.json < 100ms | Manual test |

## 3. Manual Verification (Windows)

### Bước 1: Start API
```powershell
.\venv\Scripts\Activate.ps1
uvicorn apps.api.main:app --reload --port 8000
```

### Bước 2: Test OpenAPI Endpoint
```powershell
$schema = Invoke-RestMethod -Uri "http://localhost:8000/openapi.json" -Method Get
$schema.info.title
$schema.info.version
$schema.paths.PSObject.Properties.Name
```

**Expected:**
```
YouTube AI SaaS API
1.0.0
/api/research/validate
/api/research/health
/api/collect/channel
/api/collect/health
/api/transcript/
/api/transcript/health
```

### Bước 3: Verify Schema Structure
```powershell
$schema = Invoke-RestMethod -Uri "http://localhost:8000/openapi.json" -Method Get
$schema.components.schemas.PSObject.Properties.Name
```

**Expected:** Danh sách tất cả schemas (NicheValidationResponse, etc.)

### Bước 4: Run Export Script
```powershell
python scripts/export_openapi.py
```

**Expected:**
```
✓ Saved full schema to docs\openapi_schema.json
✓ Saved schemas to docs\schemas.json
✓ Saved TypeScript types to docs\api-types.ts
```

### Bước 5: Verify Exported Files
```powershell
# Check file sizes
Get-ChildItem docs/*.json, docs/*.ts | Format-Table Name, Length

# Validate JSON
Get-Content docs/openapi_schema.json -Raw | ConvertFrom-Json | Out-Null
Write-Host "✓ openapi_schema.json is valid JSON"

Get-Content docs/schemas.json -Raw | ConvertFrom-Json | Out-Null
Write-Host "✓ schemas.json is valid JSON"
```

### Bước 6: Test Swagger UI
```powershell
Start-Process "http://localhost:8000/docs"
# Manually verify:
# - Title shows "YouTube AI SaaS API"
# - All endpoints visible
# - Tags shown correctly
# - "Try it out" button works
```

### Bước 7: Test ReDoc
```powershell
Start-Process "http://localhost:8000/redoc"
# Manually verify:
# - Documentation renders correctly
# - All sections visible
```

## 4. Sample Outputs

### /openapi.json Sample
```json
{
  "openapi": "3.0.2",
  "info": {
    "title": "YouTube AI SaaS API",
    "version": "1.0.0",
    "description": "## API Overview\n\nThis API provides..."
  },
  "paths": {
    "/api/research/validate": {
      "post": {
        "tags": ["Module 1 - Niche Validate"],
        "summary": "Validate niche viability"
      }
    }
  },
  "components": {
    "schemas": {
      "NicheValidationResponse": {
        "type": "object",
        "properties": {
          "keyword": {"type": "string"},
          "is_viable": {"type": "boolean"}
        }
      }
    }
  }
}
```

### api-types.ts Sample
```typescript
// Auto-generated from OpenAPI schema
// Do not edit manually

export interface OpenAPISchema {
  // Schema: NicheValidationResponse
  export interface NicheValidationResponse {
    keyword: string;
    is_viable: boolean;
  }
}
```

## 5. Sign-off Checklist

```
TIER 2 SELF-CHECK:

OpenAPI Schema:
  [ ] Custom schema module created
  [ ] /openapi.json returns valid JSON
  [ ] Title, version, description correct
  [ ] Tags properly assigned

Documentation:
  [ ] /docs opens Swagger UI
  [ ] /redoc opens ReDoc
  [ ] All routes have docstrings

Export:
  [ ] export_openapi.py works
  [ ] openapi_schema.json created
  [ ] schemas.json created
  [ ] api-types.ts created

Manual:
  [ ] Swagger UI renders correctly
  [ ] All endpoints visible
  [ ] Try it out works

Files Created/Modified:
  [ ] apps/api/openapi.py (NEW)
  [ ] apps/api/main.py (UPDATED)
  [ ] scripts/export_openapi.py (NEW)
  [ ] docs/openapi_schema.json (GENERATED)
  [ ] docs/schemas.json (GENERATED)
  [ ] docs/api-types.ts (GENERATED)
```

## 6. Blocker Reporting

**Nếu gặp blocker, tạo file `BLOCKERS-task-1-6.md`:**

```markdown
# BLOCKERS: Task 1.6

## Blocker 1
**Mô tả:** <Mô tả lỗi>

**Ảnh hưởng:** <Impact>

**Đề xuất:** <Suggestion>

## ...
```
