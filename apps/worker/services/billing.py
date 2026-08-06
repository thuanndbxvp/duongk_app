"""
Billing service — hold/commit/refund credits.
Phase 07: Idempotent credit management for jobs.
"""
from __future__ import annotations
from uuid import UUID


class BillingService:
    """
    Credit lifecycle: hold → commit/refund.

    Usage:
        billing = BillingService(supabase_admin)
        billing.hold(user_id, job_id, estimated_cents)
        # ... run job ...
        billing.commit(user_id, job_id, actual_cents)
        # or on failure:
        billing.refund(user_id, job_id, held_cents, actual_cents)
    """

    def __init__(self, supabase_admin):
        self.admin = supabase_admin

    def hold(self, user_id: str, job_id: str, estimated_cents: int) -> dict:
        """Hold credits for a job. Raises ValueError if insufficient."""
        result = self.admin.rpc('hold_credits', {
            'p_user_id': user_id,
            'p_amount': estimated_cents,
            'p_job_id': job_id,
        }).execute()
        if not result.data:
            raise ValueError(f'Hold failed for user {user_id}, amount {estimated_cents}')
        return {'transaction_id': result.data[0].get('transaction_id'), 'held': estimated_cents}

    def commit(self, job_id: str, actual_cents: int) -> dict:
        """Commit held credits (adjust to actual)."""
        result = self.admin.rpc('partial_commit_credits', {
            'p_job_id': job_id,
            'p_final_amount': actual_cents,
        }).execute()
        return {'committed': actual_cents, 'refunded': result.data[0].get('refund_amount', 0) if result.data else 0}

    def refund(self, job_id: str) -> int:
        """Full refund on failure."""
        result = self.admin.rpc('refund_credits', {
            'p_job_id': job_id,
        }).execute()
        return result.data[0].get('amount', 0) if result.data else 0

    def get_balance(self, user_id: str) -> int:
        """Get user's current credit balance."""
        user = self.admin.table('users').select('credits').eq('id', user_id).single().execute()
        return user.data.get('credits', 0) if user.data else 0

    def estimate_cost(self, task_type: str) -> int:
        """Estimate credit cost for a task type."""
        pricing = {
            'script_generation': 30,
            'scene_breakdown': 10,
            'tts_scene': 5,
            'render_draft': 20,
            'render_final': 50,
            'thumbnail_generation': 15,
        }
        return pricing.get(task_type, 10)
