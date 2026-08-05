# Phân bổ Kỹ năng (SKILL-ROUTING): Task 1.4 - Module 1 Niche Validate

## 1. Chiến lược tổng thể (Overall Strategy)

Module 1 Niche Validate là task backend thuần túy, không có UI. Cần:
- Skill `backend-development` để viết FastAPI routes và services
- Skill `ui-styling` KHÔNG cần thiết
- Skill `databases` chỉ để verify schema, không cần tạo migration mới

## 2. Bảng Phân bổ theo Step (Per-step Mapping)

| MSEW Step | Task ID / Tên | Primary Skill | Reference Skill | Fallback Skill | Lý do định tuyến |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Step 1 | TokenBucket Utility | `general-purpose` | `databases` | `planning` | Viết utility class thuần Python |
| Step 2 | Redis Cache với Lock | `general-purpose` | `databases` | `planning` | Async Redis operations |
| Step 3 | Formula A0 - Video Filter | `general-purpose` | `databases` | `planning` | Pure Python logic |
| Step 4 | Formula A2 - Viral Detection | `general-purpose` | `databases` | `planning` | NumPy MAD calculation |
| Step 5 | NicheValidator Service | `general-purpose` | `backend-development` | `planning` | Core business logic |
| Step 6 | API Routes & Schemas | `backend-development` | `general-purpose` | `planning` | FastAPI routes |
| Step 7 | Unit Tests | `general-purpose` | `tester` | `planning` | Viết pytest tests |

## 3. Các kỹ năng xuyên suốt (Cross-cutting Skills)

| Skill | Khi nào gọi | Mục đích |
|-------|--------------|----------|
| `general-purpose` | Mọi step | Code generation chính |
| `databases` | Verify schema | Kiểm tra Pydantic models |
| `tester` | Step 7 | Viết và chạy tests |
| `debugging` | Khi fail | Debug lỗi verify command |
| `planning` | Fallback | Khi không chắc chắn |

## 4. Files KHÔNG được đụng (Do Not Touch)

| File | Lý do |
|------|-------|
| `apps/api/main.py` | Đã có structure, chỉ import thêm routes |
| `apps/api/__init__.py` | Package init đã có |
| `apps/worker/` | Worker code thuộc task khác |
| `packages/shared-types/` | Models đã defined |

## 5. Skill Usage Commands

### Step 1-4: Utility Classes
```python
# KHÔNG cần invoke skill đặc biệt
# Viết trực tiếp với Python thuần
```

### Step 5-6: Service & Routes
```python
# Sử dụng backend-development skill pattern:
# - Async/await patterns
# - FastAPI dependency injection
# - Pydantic model validation
```

### Step 7: Testing
```powershell
pytest tests/test_module_1/ -v --cov=apps/api/modules/module_1
```

## 6. Verification Strategy

| Step | Verify Command | Expected |
|------|----------------|----------|
| 1 | `python -c "from apps.api.core.bulkhead import TokenBucket; print('OK')"` | OK |
| 2 | `python -c "from apps.api.core.cache import RedisCache; print('OK')"` | OK |
| 3 | `python -c "from apps.api.modules.module_1.formulas import filter_quality_videos; print('OK')"` | OK |
| 4 | `python -c "from apps.api.modules.module_1.formulas import detect_viral_videos; print('OK')"` | OK |
| 5 | `python -c "from apps.api.modules.module_1.service import NicheValidator; print('OK')"` | OK |
| 6 | `pytest tests/test_module_1/test_routes.py -v` | All passed |
| 7 | Coverage report | >80% |
