# Phase 1 — MSEW (Milestones / Skills / Evidence / Warnings)

## Milestones

| Step | Action | Skills | Owner |
|---|---|---|---|
| 1 | Verify 12 drift endpoints (3 fix, 9 document) | `debugging`, `code-review` | Tier 2 |
| 2 | Build `<CancelRenderButton>` component | `frontend-development`, `ui-styling` | Tier 2 |
| 3 | Wire cancel button vào `<VideoPreview>` | `frontend-development` | Tier 2 |
| 4 | Decision matrix cho 6 dead services | `code-review` | Tier 2 |
| 5 | Remove `apps/api/services/youtube.py` | `code-review`, `debugging` | Tier 2 |
| 6 | Wire `config_watcher.start_watcher()` in Celery | `backend-development`, `debugging` | Tier 2 |
| 7 | Tests: 1 component test + 1 worker test | `testing-protocol` | Tier 2 |
| 8 | Self-review qua ACCEPTANCE checklist | `code-review` | Tier 2 |
| 9 | Tier 1 review + merge | `code-review` | Tier 1 |

## Skills routing

| Task | Primary skill | Secondary |
|---|---|---|
| Component build | `frontend-development` | `ui-styling` |
| Cancel render API verify | `debugging-protocol` | `code-review` |
| Wire config_watcher | `backend-development` | `celery` (implicit) |
| Drift fix | `code-review` | `debugging-protocol` |
| Tests | `testing-protocol` | `frontend-development` |

## Evidence (test commands)

```bash
# Step 1: Verify drift
pytest tests/web/ -v -k "cancel_render" --tb=short

# Step 2-3: Component tests
pytest tests/web/components/test_cancel_render_button.tsx -v

# Step 5: No imports
grep -r "from apps.api.services.youtube" apps/ tests/
# Expected: 0 results

# Step 6: Wire test
pytest tests/worker/test_config_watcher_boot.py -v

# Step 7: Regression
pytest tests/ --tb=short -q
# Expected: ≥80% pass

# Step 8: E2E
bash scripts/run_e2e_local.sh
# Expected: exit 0
```

## Warnings

### 🟡 Gotcha 1: Cancel render semaphore

Khi cancel render, FFmpeg child process đang chạy. Backend route chỉ set `cancel_requested=true` flag. Worker `render_video.py` check flag → kill PID. **Race condition**: nếu FFmpeg exit happy trước khi worker check flag, status sẽ là `success` không phải `cancelled`.

**Fix**: Sau cancel, poll status với `setTimeout(30s)`. Nếu vẫn `running` → escalation alert.

### 🟡 Gotcha 2: Wire config_watcher = side effect

`config_watcher.start_watcher()` khởi tạo background thread. Lifecycle phức tạp:
- Worker start → thread start
- Worker stop → thread không auto-stop (leak)
- Test env → thread chạy song song với pytest

**Fix**: Trong `start_watcher()`, register `atexit` hook để cleanup. Trong test, mock `start_watcher` để không gọi thật.

### 🟡 Gotcha 3: Drift fixes phải tested

Mỗi drift fix là một hành vi quan trọng. Tier 2 PHẢI viết test cho 3 critical drift fixes:
- Test approve insight end-to-end (FE → BE → DB)
- Test cancel batch (state machine)
- Test MFA enroll (QR generated)

Đừng assume "FE đổi path → done". Backend có thể expect body khác.

### 🟡 Gotcha 4: youtube.py có thể được import trong tests

Trước khi `git rm`, grep CẢ `tests/` folder. Nếu có test reference → fix test trước, xóa sau.

```bash
grep -r "from apps.api.services.youtube" apps/ tests/
grep -r "apps.api.services.youtube" apps/ tests/
```

### 🟡 Gotcha 5: Cancel render có thể credit refund

Nếu user cancel mid-render, backend có logic refund credits trong Phase 4. Tier 2 không cần lo credit (backend tự xử lý), nhưng UI nên show "Credits đã refund" sau cancel.

## Performance budget

- Step 1-2: 4 giờ
- Step 3: 1 giờ
- Step 4-5: 1 giờ
- Step 6: 2 giờ
- Step 7-8: 4 giờ
- Total: ~12 giờ (= 1.5 ngày part-time)

## Exit gates

- [ ] All tests pass
- [ ] ≥80% coverage on new code
- [ ] No `console.log` / `print` debug statements
- [ ] No new dependencies
- [ ] LoC delta: +150 / -100 (net +50)
- [ ] Tier 1 review pass
- [ ] Merge to `launch-fix-gap` or `main`
