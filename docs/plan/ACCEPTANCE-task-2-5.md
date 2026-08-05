# Tiêu chí Nghiệm thu (ACCEPTANCE): Task 2.5

## 1. Tiêu chuẩn Chức năng

- [ ] D1 FIX: RPC handles concurrent updates
- [ ] D1 FIX: FOR UPDATE lock prevents race conditions
- [ ] ProgressTracker: start(), update(), increment(), complete(), fail()
- [ ] 14 outputs tracked
- [ ] Overall progress calculation correct
- [ ] Celery task integrates tracker

## 2. Verification Commands

```powershell
# Test RPC
psql -h localhost -U postgres -d appdk -c "SELECT update_job_sub_progress('test-job-id', 'output_1', '{\"status\": \"running\"}'::jsonb);"

# Unit tests
pytest tests/test_progress/ -v
```

## 3. Sign-off Checklist

- [ ] RPC tested
- [ ] Progress tracker works
- [ ] Unit tests pass
