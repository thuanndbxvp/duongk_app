# Rollback Procedure — AppDK Zero-to-Video

## When to Rollback
- Render pipeline regression (≥10% failure rate)
- Credit/billing miscalculation
- RLS data leak
- Migration fails or corrupts data

## Rollback Steps

### 1. Stop New Jobs
```bash
# Pause Celery worker render queue
docker compose stop worker-render
# Set maintenance mode
export MAINTENANCE_MODE=true
```

### 2. Revert Migration (if applicable)
```bash
# Each migration is backward-compatible with nullable FK
# To rollback: create reverse migration
supabase db diff --linked -f rollback_<number>.sql
supabase db push
```

### 3. Revert Deployment
```bash
# Git checkout last known good commit
git checkout <last-good-commit-sha>
# Rebuild + restart
docker compose up -d --build
```

### 4. Verify
```bash
# Run smoke tests
pytest tests/e2e/test_pipeline_e2e.py -v
# Check health
curl http://localhost:8000/health
# Verify RLS
pytest tests/integration/test_rls.py -v
```

### 5. Resume
```bash
export MAINTENANCE_MODE=false
docker compose start worker-render
```

## Data Recovery
- **Asset variants:** Original source never mutated, variants are additive rows
- **Timelines:** Versioned, rollback to previous version
- **Voice lines:** Per-scene, retry individual scenes
- **Render jobs:** Failed jobs retry with `retry_count` increment

## Emergency Contacts
- Tier 1 (Planner): Review AUDIT-REPORT before any code push
- Tier 2 (Engineer): Execute rollback steps above
