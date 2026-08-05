# Tiêu chí Nghiệm thu (ACCEPTANCE): Task 1.4 - Module 1 Niche Validate

## 1. Tiêu chuẩn Chức năng (Functional Criteria)

### Core Features
- [ ] **TokenBucket Utility** hoạt động đúng:
  - [ ] `acquire()` trả về True khi có đủ tokens
  - [ ] `acquire()` blocking đúng timeout
  - [ ] Tokens được refill đúng rate

- [ ] **Redis Cache với Lock** hoạt động:
  - [ ] Cache hit trả về đúng giá trị
  - [ ] Cache miss gọi factory và lưu cache
  - [ ] Distributed lock ngăn stampede (chỉ 1 worker generate)

- [ ] **Formula A0 (Video Filter)** hoạt động:
  - [ ] Lọc được Shorts (<60 giây)
  - [ ] Lọc được Live streams
  - [ ] Lọc được videos có <1000 views
  - [ ] Lọc được videos quá 2 năm tuổi
  - [ ] Giữ lại quality videos

- [ ] **Formula A2 (Viral Detection)** hoạt động:
  - [ ] Phát hiện outliers với MAD threshold = 3.5
  - [ ] Trả về empty list khi views đều nhau
  - [ ] Xử lý đúng sample <5 videos

- [ ] **NicheValidator Service** hoạt động:
  - [ ] Gọi Pytrends thành công
  - [ ] Fallback sang SerpAPI khi Pytrends fail
  - [ ] Cache results đúng 24h
  - [ ] Trả về response đúng schema

- [ ] **API Routes** hoạt động:
  - [ ] `POST /api/research/validate` trả về 200
  - [ ] `GET /api/research/health` trả về 200
  - [ ] Error handling trả về 4xx/5xx phù hợp

### Sample Response Verification
```json
{
  "keyword": "làm đẹp",
  "total_monthly_views": 15000000,
  "total_channels": 45,
  "avg_views_per_video": 45000,
  "google_trends_interest": 72,
  "is_viable": true,
  "suggested_titles": [
    "5 công thức làm đẹp từ thiên nhiên",
    "Cách chăm sóc da mùa đông"
  ]
}
```

## 2. Tiêu chuẩn Phi chức năng (Non-functional)

| Tiêu chí | Yêu cầu | Verification |
|----------|---------|--------------|
| **Hiệu năng** | API response < 500ms (cache hit) | Manual test |
| **Hiệu năng** | API response < 5s (cache miss) | Manual test |
| **Rate Limit** | Pytrends không exceed quota | Monitor logs |
| **Cache** | Cache TTL = 24h | Check Redis TTL |
| **Dependencies** | Pytrends, SerpAPI, Redis hoạt động | Integration tests |

## 3. Mục tiêu Test Coverage

| Metric | Target | Priority |
|--------|--------|----------|
| Overall coverage | ≥80% | HIGH |
| Formula coverage | 100% | HIGH |
| Service coverage | ≥70% | MEDIUM |
| Routes coverage | ≥60% | MEDIUM |

## 4. Các bước Manual Verification (Windows)

### Bước 1: Khởi động Redis
```powershell
# Start Redis (nếu chưa chạy)
redis-server
```

### Bước 2: Khởi động API
```powershell
.\venv\Scripts\Activate.ps1
cd d:\appDK
uvicorn apps.api.main:app --reload --port 8000
```

### Bước 3: Test Health Endpoint
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/research/health" -Method Get
```

**Expected:**
```json
{
  "status": "healthy",
  "module": "niche_validate",
  "version": "1.0.0"
}
```

### Bước 4: Test Validation Endpoint
```powershell
$body = @{
    keyword = "làm đẹp"
    user_id = "test"
    use_cache = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/research/validate" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Expected:** Response với `is_viable`, `suggested_titles`, etc.

### Bước 5: Test Caching
```powershell
# Gọi 2 lần, lần 2 phải nhanh hơn (cache hit)
Invoke-RestMethod -Uri "http://localhost:8000/api/research/validate" `
    -Method Post `
    -ContentType "application/json" `
    -Body '{"keyword":"làm đẹp","use_cache":true}'
```

### Bước 6: Chạy Unit Tests
```powershell
pytest tests/test_module_1/ -v --cov=apps/api/modules/module_1 --cov-report=term-missing
```

### Bước 7: Verify Coverage
```powershell
# Check coverage report
pytest tests/test_module_1/ --cov=apps/api/modules/module_1 --cov-report=html
# Open htmlcov/index.html in browser
```

## 5. Sign-off Checklist

```
TIER 2 SELF-CHECK:

Code Quality:
  [ ] Linter passed (no errors)
  [ ] Type hints complete
  [ ] Docstrings present
  [ ] No TODO comments

Testing:
  [ ] All unit tests pass
  [ ] Coverage ≥ 80%
  [ ] Manual verification done

Documentation:
  [ ] Code comments (if needed)
  [ ] README updated (if needed)

Files Created/Modified:
  [ ] apps/api/core/bulkhead.py (NEW)
  [ ] apps/api/core/cache.py (NEW)
  [ ] apps/api/modules/module_1/formulas.py (NEW)
  [ ] apps/api/modules/module_1/service.py (NEW)
  [ ] apps/api/modules/module_1/schemas.py (NEW)
  [ ] apps/api/modules/module_1/routes.py (NEW)
  [ ] apps/api/modules/module_1/__init__.py (NEW)
  [ ] apps/api/main.py (UPDATED)
  [ ] tests/test_module_1/ (NEW)
```

## 6. Blocker Reporting

**Nếu gặp blocker, tạo file `BLOCKERS-task-1-4.md`:**

```markdown
# BLOCKERS: Task 1.4

## Blocker 1
**Mô tả:** <Mô tả lỗi>

**Ảnh hưởng:** <Impact>

**Đề xuất:** <Suggestion>

## ...
```
