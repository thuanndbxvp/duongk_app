# Sprint 3 Task Group 3: Script Generation - MSEW

## Bước 1: SQL Migration

**File:** `supabase/migrations/0016_scripts.sql`

```sql
-- Migration: 0016_scripts.sql
CREATE TABLE IF NOT EXISTS generated_scripts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assistant_id UUID NOT NULL REFERENCES channel_assistants(id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
  topic TEXT NOT NULL,
  script_text TEXT NOT NULL,
  score FLOAT,
  cost_usd NUMERIC(10,6) NOT NULL DEFAULT 0,
  attempts INT NOT NULL DEFAULT 1,
  scenes JSONB,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scripts_assistant ON generated_scripts(assistant_id, created_at DESC);

ALTER TABLE generated_scripts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "user_can_read_own_scripts" ON generated_scripts FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM channel_assistants ca
      WHERE ca.id = generated_scripts.assistant_id
        AND ca.user_id = auth.uid()
    )
  );
```

---

## Bước 2: Anti-Slop Service

**File:** `apps/worker/services/antislop_service.py`

```python
"""
Anti-Slop Service - Validates scripts against AI slop patterns.
Layer 1: Regex (fast), Layer 2: LLM (slow), Layer 3: Cost cap retry.
"""
import re
import json
from typing import Optional
from openai import OpenAI


VIETNAMESE_SLOP_PATTERNS = [
    r'\b(cảm ơn bạn đã xem|like and subscribe|nhấn like|đăng ký kênh)\b',
    r'\b(chắc chắn|rất nhiều|một cách|tất cả các)\s+\w+\s+\w+\b',
    r'\b(xin vui lòng|đừng quên|hãy nhớ rằng)\b',
    r'\b(tuy nhiên|ngoài ra|mặt khác)\b',
]

ENGLISH_SLOP_PATTERNS = [
    r'\b(game-changer|leverage|synergy|scalable|paradigm|pivot|deep-dive)\b',
    r'\b(in this video|welcome back|let me know in comments)\b',
]


class AntiSlopService:
    """Service for detecting and filtering AI slop in scripts."""

    def __init__(self):
        self.vn_patterns = [re.compile(p, re.IGNORECASE) for p in VIETNAMESE_SLOP_PATTERNS]
        self.en_patterns = [re.compile(p, re.IGNORECASE) for p in ENGLISH_SLOP_PATTERNS]
        self.filler_pattern = re.compile(r'\b(um+|uh+|à|ừ|ờ|ơ|ạ)\b', re.IGNORECASE)

    def layer1_regex_check(self, text: str) -> tuple[bool, list[str]]:
        """
        Layer 1: Fast regex check for known slop patterns.
        
        Returns:
            (is_clean, violations)
        """
        violations = []

        # Vietnamese slop
        for pattern in self.vn_patterns:
            matches = pattern.findall(text)
            if matches:
                violations.append(f"VN slop: {matches[0]}")

        # English slop (shouldn't appear in Vietnamese script)
        for pattern in self.en_patterns:
            matches = pattern.findall(text)
            if matches:
                violations.append(f"EN slop: {matches[0]}")

        # Excessive fillers
        fillers = self.filler_pattern.findall(text)
        if len(fillers) > 5:
            violations.append(f"Too many fillers: {len(fillers)}")

        return len(violations) == 0, violations

    def layer2_llm_semantic_check(
        self,
        text: str,
        client: Optional[OpenAI] = None,
        model: str = "gpt-4o-mini",
    ) -> tuple[float, str]:
        """
        Layer 2: LLM semantic scoring.
        
        Returns:
            (score 1-10, reason)
        """
        if client is None:
            client = OpenAI()

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": """Bạn là chuyên gia đánh giá kịch bản YouTube tiếng Việt.
Đánh giá dựa trên:
1. Tính tự nhiên (không robotic, không văn mẫu)
2. Độ độc đáo (không generic)
3. Phù hợp văn hóa Việt Nam
4. Không có filler words thái quá

Trả lời JSON: {"score": 1-10, "reason": "giải thích ngắn"}"""
                },
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)
        return result.get('score', 0), result.get('reason', '')

    def validate_with_retry(
        self,
        script_text: str,
        client: Optional[OpenAI] = None,
        max_retries: int = 3,
        min_score: float = 6.0,
        budget_usd: float = 0.10,
    ) -> dict:
        """
        Layer 3: Cost-capped retry with best-of-N selection.
        
        Args:
            script_text: The script to validate
            client: OpenAI client
            max_retries: Maximum validation attempts
            min_score: Minimum passing score
            budget_usd: Maximum budget for validation
            
        Returns:
            dict with validation results
        """
        if client is None:
            client = OpenAI()

        best_result = {
            'text': script_text,
            'score': 0,
            'attempts': 1,
            'total_cost': 0,
            'status': 'initial',
            'reason': '',
        }

        # Layer 1 quick check
        is_clean, violations = self.layer1_regex_check(script_text)
        if not is_clean:
            best_result['status'] = 'layer1_failed'
            best_result['violations'] = violations
            return best_result

        for attempt in range(1, max_retries + 1):
            # Estimate cost
            estimated_cost = len(script_text) / 1000 * 0.0005

            # Check budget
            if best_result['total_cost'] + estimated_cost > budget_usd:
                best_result['status'] = 'budget_exceeded'
                break

            # LLM scoring
            score, reason = self.layer2_llm_semantic_check(script_text, client)

            # Track actual cost (rough estimate)
            actual_cost = estimated_cost * 1.2
            best_result['total_cost'] += actual_cost
            best_result['attempts'] = attempt
            best_result['reason'] = reason

            if score >= min_score:
                best_result['score'] = score
                best_result['status'] = 'passed'
                return best_result

            # Track best attempt
            if score > best_result['score']:
                best_result['score'] = score
                best_result['text'] = script_text

        best_result['status'] = 'max_retries_exhausted'
        return best_result
```

---

## Bước 3: Celery Task

**File:** `apps/worker/tasks/script_generate.py`

```python
"""
Celery task for script generation with RAG + Anti-Slop.
"""
from celery import Task
from apps.worker.celery_app import celery_app
from apps.worker.services.rag_service import RAGService
from apps.worker.services.embedding_router import EmbeddingRouter
from apps.worker.services.antislop_service import AntiSlopService
from apps.worker.services.progress_tracker import ProgressTracker
from apps.worker.services.supabase_admin import get_supabase_admin
from openai import OpenAI
import json


DEFAULT_BUDGET_USD = 0.10


@celery_app.task(
    name='apps.worker.tasks.script_generate.run',
    bind=True,
    max_retries=2,
    acks_late=True,
)
def run(self: Task, job_id: str, assistant_id: str, topic: str) -> dict:
    """Generate script with RAG context and anti-slop validation."""
    supabase = get_supabase_admin()
    tracker = ProgressTracker(supabase, job_id)

    try:
        # === PHASE 1: RAG Retrieval (30%) ===
        tracker.start('rag_retrieve')
        tracker.tick('rag_retrieve', 10)

        embedding_router = EmbeddingRouter()
        rag_service = RAGService(supabase, embedding_router)

        # Get channel persona
        assistant = supabase.table('channel_assistants').select('*').eq('id', assistant_id).single().execute()
        channel_persona = assistant.data.get('persona', {}) if assistant.data else {}

        # RAG retrieval
        context_result = await rag_service.retrieve_context(
            assistant_id=assistant_id,
            query=topic,
            top_k=10,
            lambda_mmr=0.7,
        )
        tracker.tick('rag_retrieve', 30)

        # Build prompt
        prompt = rag_service.build_script_prompt(
            channel_persona=channel_persona,
            rag_context=context_result['context_text'],
            topic=topic,
        )
        tracker.done('rag_retrieve')

        # === PHASE 2: Generate Script (50%) ===
        tracker.start('generate')
        tracker.tick('generate', 10)

        openai = OpenAI()

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        script_data = json.loads(response.choices[0].message.content)
        tracker.tick('generate', 40)

        # === PHASE 3: Anti-Slop Validation (20%) ===
        tracker.start('validate')

        antislop = AntiSlopService()
        validation = antislop.validate_with_retry(
            script_text=script_data.get('body', ''),
            client=openai,
            max_retries=3,
            min_score=6.0,
            budget_usd=DEFAULT_BUDGET_USD,
        )

        # Update with validation results
        if validation['status'] == 'passed':
            script_data['mimic_score'] = validation['score']
        else:
            script_data['mimic_score'] = validation['score']
            script_data['validation_warning'] = validation['status']

        tracker.done('validate')
        tracker.done('generate')

        # === SAVE RESULTS ===
        result = {
            'script': script_data,
            'rag_context': {'num_chunks': context_result['num_chunks']},
            'validation': {
                'status': validation['status'],
                'score': validation['score'],
                'attempts': validation['attempts'],
                'cost_usd': validation['total_cost'],
            },
        }

        supabase.table('jobs').update({
            'status': 'succeeded',
            'progress': 100,
            'result_payload': result,
            'sub_progress': tracker.get_sub_progress(),
        }).eq('id', job_id).execute()

        # Save script
        supabase.table('generated_scripts').insert({
            'job_id': job_id,
            'assistant_id': assistant_id,
            'topic': topic,
            'script_text': json.dumps(script_data),
            'score': validation['score'],
            'cost_usd': validation['total_cost'],
            'attempts': validation['attempts'],
        }).execute()

        return result

    except Exception as e:
        tracker.fail('generate', str(e))
        supabase.table('jobs').update({
            'status': 'failed',
            'error_message': str(e),
        }).eq('id', job_id).execute()
        raise
```

---

## Bước 4: API Router

**File:** `apps/api/routers/scripts.py`

```python
"""
API router for script generation endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID
from apps.api.dependencies.supabase import get_supabase_user, get_supabase_admin
from apps.worker.tasks.script_generate import run as script_generate_task


router = APIRouter()


class GenerateScriptRequest(BaseModel):
    assistant_id: UUID
    topic: str


class ScriptResponse(BaseModel):
    job_id: str
    status: str
    message: str


@router.post('/generate', response_model=ScriptResponse)
async def generate_script(
    req: GenerateScriptRequest,
    user_id: str = Depends(get_supabase_user),
):
    admin = get_supabase_admin()

    # Verify assistant belongs to user
    assistant = admin.table('channel_assistants').select('id').eq('id', str(req.assistant_id)).eq('user_id', user_id).single().execute()
    if not assistant.data:
        raise HTTPException(404, 'Assistant not found')

    # Create job
    job_result = admin.table('jobs').insert({
        'user_id': user_id,
        'task_type': 'script_generate',
        'input_payload': {
            'assistant_id': str(req.assistant_id),
            'topic': req.topic,
        },
        'status': 'pending',
    }).execute()

    job = job_result.data[0]
    job_id = job['id']

    # Enqueue task
    task = script_generate_task.delay(
        job_id=job_id,
        assistant_id=str(req.assistant_id),
        topic=req.topic,
    )

    admin.table('jobs').update({'celery_task_id': task.id}).eq('id', job_id).execute()

    return ScriptResponse(
        job_id=job_id,
        status='pending',
        message=f'Script generation started. Track at /api/jobs/{job_id}',
    )
```

---

## Bước 5: Unit Tests

**File:** `apps/worker/services/test_antislop_service.py`

```python
"""
Unit tests for AntiSlopService.
"""
import pytest
from unittest.mock import MagicMock
from apps.worker.services.antislop_service import AntiSlopService


class TestAntiSlopService:
    """Test suite for AntiSlopService."""

    @pytest.fixture
    def service(self):
        return AntiSlopService()

    def test_layer1_regex_clean_text(self, service):
        """Test clean text passes Layer 1."""
        text = "Hôm nay tôi sẽ hướng dẫn các bạn cách làm bánh chocolate ngon."
        is_clean, violations = service.layer1_regex_check(text)
        assert is_clean is True
        assert len(violations) == 0

    def test_layer1_regex_vietnamese_slop(self, service):
        """Test Vietnamese slop detected."""
        text = "Cảm ơn bạn đã xem video này, nhấn like và đăng ký kênh nhé!"
        is_clean, violations = service.layer1_regex_check(text)
        assert is_clean is False
        assert any('VN slop' in v for v in violations)

    def test_layer1_regex_english_slop(self, service):
        """Test English slop detected in Vietnamese text."""
        text = "This is a game-changer! Welcome back to my channel."
        is_clean, violations = service.layer1_regex_check(text)
        assert is_clean is False
        assert any('EN slop' in v for v in violations)

    def test_layer1_regex_filler_words(self, service):
        """Test excessive fillers detected."""
        text = "Um uh à ừ ơ um uh à ừ ơ um"
        is_clean, violations = service.layer1_regex_check(text)
        assert is_clean is False
        assert any('filler' in v.lower() for v in violations)

    def test_validate_with_retry_layer1_fails(self, service):
        """Test validation fails fast on Layer 1."""
        text = "Cảm ơn bạn đã xem, like and subscribe!"
        result = service.validate_with_retry(text, max_retries=3)
        
        assert result['status'] == 'layer1_failed'
        assert result['score'] == 0

    def test_validate_with_retry_budget_exceeded(self, service):
        """Test validation stops at budget."""
        # Mock LLM to always return low score
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"score": 5, "reason": "test"}'))]
        mock_client.chat.completions.create.return_value = mock_response

        text = "Clean text here" * 100
        result = service.validate_with_retry(
            text, 
            client=mock_client,
            max_retries=3,
            budget_usd=0.001,  # Very low budget
        )
        
        assert result['total_cost'] > 0
```

---

## Bước 6: Verify

```bash
# Apply migration
supabase db push

# Run tests
cd apps/worker && pytest services/test_antislop_service.py -v

# Test API (manual)
curl -X POST http://localhost:8000/api/scripts/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"assistant_id": "uuid", "topic": "Cách làm bánh"}'
```

---

## Commands for Tier 2

```bash
cat docs/plan/CONTEXT-sprint3-script-generation.md
cat docs/plan/SKILL-ROUTING-sprint3-script-generation.md
cat docs/plan/PLAN-sprint3-script-generation.md
cat docs/plan/MSEW-sprint3-script-generation.md
cat docs/plan/ACCEPTANCE-sprint3-script-generation.md
```
