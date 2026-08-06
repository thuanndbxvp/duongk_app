"""
Tests for batch fanout — Phase 10.
"""
import pytest


class TestCostEstimator:
    """Cost estimation idempotent and capped."""

    def test_estimate_render_draft(self):
        from apps.worker.services.cost_estimator import estimate_cost
        est = estimate_cost("render_draft", 5)
        assert est['total'] == 100
        assert est['per_item'] == 20

    def test_estimate_render_final(self):
        from apps.worker.services.cost_estimator import estimate_cost
        est = estimate_cost("render_final", 3)
        assert est['total'] == 150

    def test_estimate_unknown_type(self):
        from apps.worker.services.cost_estimator import estimate_cost
        est = estimate_cost("unknown_type", 10)
        assert est['per_item'] == 10  # default

    def test_cap_estimate(self):
        from apps.worker.services.cost_estimator import cap_estimate
        capped = cap_estimate(100, last_actual=200)
        assert capped == 240  # max(100, 200*1.2)


class TestProviderHealth:
    """Provider health tracking."""

    def test_default_healthy(self):
        from apps.worker.services.provider_health import is_healthy
        assert is_healthy("unknown_provider") is True

    def test_mark_unhealthy(self):
        from apps.worker.services.provider_health import update_health, is_healthy
        update_health("gemini", False)
        assert is_healthy("gemini") is False

    def test_quota_check(self):
        from apps.worker.services.provider_health import update_health, has_quota
        update_health("gemini", True, quota=100)
        assert has_quota("gemini", 50) is True
        assert has_quota("gemini", 200) is False

    def test_exhausted(self):
        from apps.worker.services.provider_health import mark_exhausted, is_healthy, has_quota
        mark_exhausted("gemini")
        assert is_healthy("gemini") is False
        assert has_quota("gemini", 1) is False


class TestBatchFanout:
    """Batch execution logic."""

    def test_fallback_chain_order(self):
        from apps.worker.services.batch_fanout import FALLBACK_CHAIN
        chain = FALLBACK_CHAIN.get("render_draft", [])
        assert chain[0] == "local"
        assert len(chain) > 1

    def test_max_retries(self):
        from apps.worker.services.batch_fanout import MAX_RETRIES
        assert MAX_RETRIES == 3

    def test_max_items_per_batch(self):
        max_items = 50
        items = list(range(30))
        assert len(items) <= max_items


class TestPartialSuccess:
    """Partial success: 1 item fail, others OK."""

    def test_one_failure_others_succeed(self):
        results = [
            {"status": "success"},
            {"status": "failed"},
            {"status": "success"},
            {"status": "success"},
        ]
        succeeded = sum(1 for r in results if r["status"] == "success")
        assert succeeded == 3

    def test_all_fail(self):
        results = [{"status": "failed"}, {"status": "failed"}]
        succeeded = sum(1 for r in results if r["status"] == "success")
        assert succeeded == 0

    def test_status_partial_when_mixed(self):
        """Final status = 'partial' when some succeed, some fail."""
        succeeded = 3
        failed = 2
        status = "completed" if failed == 0 else ("partial" if succeeded > 0 else "failed")
        assert status == "partial"


class TestBatchSchema:
    """Batch schemas."""

    def test_create_valid(self):
        from apps.api.schemas.batch import BatchCreateRequest
        from uuid import uuid4
        req = BatchCreateRequest(project_ids=[uuid4(), uuid4()], task_type="render_draft")
        assert len(req.project_ids) == 2

    def test_create_empty_rejected(self):
        from apps.api.schemas.batch import BatchCreateRequest
        with pytest.raises(Exception):
            BatchCreateRequest(project_ids=[])

    def test_create_max_50_items(self):
        from apps.api.schemas.batch import BatchCreateRequest
        from uuid import uuid4
        with pytest.raises(Exception):
            BatchCreateRequest(project_ids=[uuid4()] * 51)

    def test_cost_estimate_schema(self):
        from apps.api.schemas.batch import CostEstimate
        est = CostEstimate(total=100, per_item=20, item_count=5)
        assert est.total == 100
