# Sprint 4 Task Group 3: Credit System - MSEW

## Bước 1: SQL Migration

**File:** `supabase/migrations/0018_credit_tiers.sql`

```sql
-- ============================================================
-- Migration: 0018_credit_tiers.sql
-- Purpose: Credit tiers + helper functions
-- ============================================================

-- Update users table to add tier-specific defaults
ALTER TABLE users 
  ALTER COLUMN credits SET DEFAULT 100,
  ALTER COLUMN tier SET DEFAULT 'free';

-- Credit pricing table
CREATE TABLE IF NOT EXISTS credit_pricing (
  job_type TEXT PRIMARY KEY,
  credits INT NOT NULL,
  description TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO credit_pricing (job_type, credits, description) VALUES
  ('niche_validate', 5, 'Validate a YouTube niche'),
  ('collect_channel', 10, 'Collect metadata + transcripts'),
  ('deep_analysis', 50, 'Run 14-output deep analysis'),
  ('script_generation', 30, 'Generate AI script with RAG'),
  ('scene_breakdown', 10, 'Break script into scenes with B-roll'),
  ('idea_generation', 5, 'Generate HDBSCAN-based ideas'),
  ('rag_retrieve', 1, 'RAG context retrieval')
ON CONFLICT (job_type) DO NOTHING;

-- Hold credits function (atomic)
CREATE OR REPLACE FUNCTION hold_credits(
  p_user_id UUID,
  p_amount INT,
  p_job_id UUID
) RETURNS TABLE(
  transaction_id UUID,
  balance_after INT
) AS $$
DECLARE
  v_current_balance INT;
  v_tx_id UUID;
BEGIN
  -- Lock user row
  SELECT credits INTO v_current_balance
  FROM users WHERE id = p_user_id FOR UPDATE;
  
  IF v_current_balance IS NULL THEN
    RAISE EXCEPTION 'User not found';
  END IF;
  
  IF v_current_balance < p_amount THEN
    RAISE EXCEPTION 'Insufficient credits: have %, need %', v_current_balance, p_amount;
  END IF;
  
  -- Deduct
  UPDATE users SET credits = credits - p_amount WHERE id = p_user_id;
  
  -- Record transaction
  INSERT INTO credit_transactions (user_id, amount, job_id, job_type, metadata)
  VALUES (p_user_id, -p_amount, p_job_id, 'hold', jsonb_build_object('status', 'pending'))
  RETURNING id INTO v_tx_id;
  
  RETURN QUERY SELECT v_tx_id, v_current_balance - p_amount;
END;
$$ LANGUAGE plpgsql;

-- Refund credits (on failure)
CREATE OR REPLACE FUNCTION refund_credits(
  p_job_id UUID
) RETURNS INT AS $$
DECLARE
  v_tx RECORD;
  v_refund INT;
BEGIN
  SELECT * INTO v_tx FROM credit_transactions
  WHERE job_id = p_job_id AND metadata->>'status' = 'pending'
  LIMIT 1;
  
  IF v_tx IS NULL THEN
    RETURN 0;
  END IF;
  
  v_refund := ABS(v_tx.amount);
  
  -- Refund
  UPDATE users SET credits = credits + v_refund WHERE id = v_tx.user_id;
  
  -- Mark transaction as refunded
  UPDATE credit_transactions
  SET metadata = jsonb_set(metadata, '{status}', '"refunded"')
  WHERE id = v_tx.id;
  
  RETURN v_refund;
END;
$$ LANGUAGE plpgsql;
```

---

## Bước 2: Credit Manager

**File:** `apps/api/services/credit_manager.py`

```python
"""
Credit Manager - Hold/Adjust/Commit/Refund pattern.
"""
from typing import Optional
from uuid import UUID
from apps.api.dependencies.supabase import get_supabase_admin


PRICING = {
    'niche_validate': 5,
    'collect_channel': 10,
    'deep_analysis': 50,
    'script_generation': 30,
    'scene_breakdown': 10,
    'idea_generation': 5,
    'rag_retrieve': 1,
}


class CreditManager:
    """Service for managing user credits."""
    
    def __init__(self):
        self.admin = get_supabase_admin()
    
    def get_pricing(self, job_type: str) -> int:
        """Get credit cost for a job type."""
        return PRICING.get(job_type, 0)
    
    def get_balance(self, user_id: str) -> int:
        """Get user's current credit balance."""
        user = (
            self.admin.table('users')
            .select('credits')
            .eq('id', user_id)
            .single()
            .execute()
        )
        return user.data['credits'] if user.data else 0
    
    def hold(self, user_id: str, job_id: str, amount: int) -> dict:
        """
        Hold credits for a job (atomic).
        
        Raises:
            ValueError: Insufficient credits or user not found
        """
        result = self.admin.rpc('hold_credits', {
            'p_user_id': user_id,
            'p_amount': amount,
            'p_job_id': job_id,
        }).execute()
        
        if not result.data:
            raise ValueError('Hold failed')
        
        return {
            'transaction_id': result.data[0]['transaction_id'],
            'balance_after': result.data[0]['balance_after'],
        }
    
    def adjust(self, job_id: str, final_amount: int) -> dict:
        """
        Adjust hold to final amount (refund difference).
        """
        result = self.admin.rpc('partial_commit_credits', {
            'p_job_id': job_id,
            'p_final_amount': final_amount,
        }).execute()
        
        return {
            'refund_amount': result.data[0].get('refund_amount', 0) if result.data else 0,
        }
    
    def commit(self, job_id: str) -> None:
        """Mark transaction as committed."""
        self.admin.table('credit_transactions').update({
            'metadata': {'status': 'committed'},
        }).eq('job_id', job_id).execute()
    
    def refund(self, job_id: str) -> int:
        """Refund credits on failure."""
        result = self.admin.rpc('refund_credits', {
            'p_job_id': job_id,
        }).execute()
        
        return result.data if result.data else 0
```

---

## Bước 3: Credit Dependency

**File:** `apps/api/dependencies/credit_required.py`

```python
"""
Dependency for charging credits before processing.
"""
from fastapi import HTTPException, Depends
from apps.api.dependencies.auth import get_supabase_user
from apps.api.services.credit_manager import CreditManager


def credit_required(
    job_type: str,
    user_id: str = Depends(get_supabase_user),
):
    """
    Check user has enough credits, then hold.
    
    Args:
        job_type: Type of job (must be in PRICING)
        user_id: From JWT (auto-injected)
        
    Raises:
        HTTPException: 402 if insufficient credits
    """
    manager = CreditManager()
    cost = manager.get_pricing(job_type)
    
    if cost == 0:
        return
    
    balance = manager.get_balance(user_id)
    if balance < cost:
        raise HTTPException(
            status_code=402,
            detail=f'Insufficient credits: have {balance}, need {cost}',
        )
```

---

## Bước 4: Credits Router

**File:** `apps/api/routers/credits.py`

```python
from fastapi import APIRouter, Depends
from apps.api.dependencies.auth import get_supabase_user
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.services.credit_manager import CreditManager


router = APIRouter()


@router.get('/credits/balance')
async def get_balance(user_id: str = Depends(get_supabase_user)):
    """Get current credit balance."""
    manager = CreditManager()
    return {
        'credits': manager.get_balance(user_id),
        'tier': _get_user_tier(user_id),
    }


@router.get('/credits/transactions')
async def get_transactions(user_id: str = Depends(get_supabase_user)):
    """Get credit transaction history."""
    admin = get_supabase_admin()
    result = (
        admin.table('credit_transactions')
        .select('*, jobs(task_type)')
        .eq('user_id', user_id)
        .order('created_at', desc=True)
        .limit(50)
        .execute()
    )
    return result.data


def _get_user_tier(user_id: str) -> str:
    admin = get_supabase_admin()
    user = admin.table('users').select('tier').eq('id', user_id).single().execute()
    return user.data['tier'] if user.data else 'free'
```

---

## Bước 5: Unit Tests

**File:** `apps/api/test_credit_manager.py`

```python
import pytest
from unittest.mock import MagicMock
from apps.api.services.credit_manager import CreditManager


class TestCreditManager:
    @pytest.fixture
    def mock_admin(self):
        return MagicMock()
    
    @pytest.fixture
    def manager(self, mock_admin, monkeypatch):
        monkeypatch.setattr('apps.api.services.credit_manager.get_supabase_admin', lambda: mock_admin)
        return CreditManager()
    
    def test_get_pricing(self, manager):
        assert manager.get_pricing('script_generation') == 30
        assert manager.get_pricing('rag_retrieve') == 1
        assert manager.get_pricing('unknown') == 0
    
    def test_get_balance(self, manager, mock_admin):
        mock_admin.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={'credits': 100}
        )
        assert manager.get_balance('user-1') == 100
    
    def test_hold_succeeds(self, manager, mock_admin):
        mock_admin.rpc.return_value.execute.return_value = MagicMock(
            data=[{'transaction_id': 'tx-1', 'balance_after': 70}]
        )
        result = manager.hold('user-1', 'job-1', 30)
        assert result['balance_after'] == 70
    
    def test_hold_insufficient_raises(self, manager, mock_admin):
        # Simulate RPC failure
        mock_admin.rpc.return_value.execute.return_value = MagicMock(data=[])
        with pytest.raises(ValueError):
            manager.hold('user-1', 'job-1', 30)
```

---

## Bước 6: Verify

```bash
# Apply migration
supabase db push

# Run tests
cd apps/api
pytest test_credit_manager.py -v
```

---

## Commands for Tier 2

```bash
cat docs/plan/CONTEXT-sprint4-credit-system.md
cat docs/plan/SKILL-ROUTING-sprint4-credit-system.md
cat docs/plan/PLAN-sprint4-credit-system.md
cat docs/plan/MSEW-sprint4-credit-system.md
cat docs/plan/ACCEPTANCE-sprint4-credit-system.md
```
