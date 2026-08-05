# Sprint 3 Task Group 4: Scene Breakdown - MSEW

## Bước 1: SceneBreaker Service

**File:** `apps/worker/services/scene_breaker.py`

```python
"""
Scene Breaker Service - Segment script into scenes with B-roll data.
"""
import re
import json
from typing import Optional
from openai import OpenAI


BROLL_PATTERNS = [
    (r'đang\s+(.+?)(?:\s+|,|\.|$)', 'doing'),
    (r'tại\s+(.+?)(?:\s+|,|\.|$)', 'location'),
    (r'nấu\s+(.+?)(?:\s+|,|\.|$)', 'cooking'),
    (r'làm\s+(.+?)(?:\s+|,|\.|$)', 'making'),
    (r'cho\s+(.+?)\s+ăn(?:\s+|,|\.|$)', 'food_prep'),
]


class SceneBreaker:
    """Service for segmenting scripts into scenes."""

    def __init__(self, default_wpm: int = 150):
        """
        Initialize SceneBreaker.
        
        Args:
            default_wpm: Default words per minute for speech
        """
        self.default_wpm = default_wpm
        self.broll_patterns = [(re.compile(p, re.IGNORECASE), ctx) for p, ctx in BROLL_PATTERNS]

    def segment_scenes(
        self,
        script_text: str,
        pacing_wpm: Optional[int] = None,
        target_duration_minutes: int = 10,
    ) -> list[dict]:
        """
        Segment script into scenes based on WPM.
        
        Args:
            script_text: Full script text
            pacing_wpm: Override WPM from channel profile
            target_duration_minutes: Target total duration
            
        Returns:
            List of scene dictionaries
        """
        wpm = pacing_wpm or self.default_wpm

        # Split by paragraphs
        paragraphs = [p.strip() for p in script_text.split('\n\n') if p.strip()]

        scenes = []
        current_time = 0.0

        for i, para in enumerate(paragraphs):
            words = len(para.split())
            duration_minutes = words / wpm
            duration_seconds = duration_minutes * 60

            scenes.append({
                'scene_number': i + 1,
                'start_time': round(current_time, 1),
                'end_time': round(current_time + duration_seconds, 1),
                'duration_seconds': round(duration_seconds, 1),
                'text': para,
                'word_count': words,
                'broll_keywords': self._extract_broll_keywords(para),
            })

            current_time += duration_seconds

        return scenes

    def _extract_broll_keywords(self, text: str) -> list[str]:
        """
        Extract Vietnamese keywords for B-roll search.
        
        Args:
            text: Scene text
            
        Returns:
            List of extracted keywords
        """
        keywords = []

        for pattern, context in self.broll_patterns:
            matches = pattern.findall(text)
            for match in matches:
                # Clean up
                keyword = match.strip() if isinstance(match, str) else ' '.join(match).strip()
                if keyword and len(keyword) > 2:
                    keywords.append(keyword)

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for kw in keywords:
            if kw.lower() not in seen:
                seen.add(kw.lower())
                unique.append(kw)

        return unique[:5]  # Max 5 keywords per scene

    async def translate_broll_keywords(
        self,
        keywords: list[str],
        client: Optional[OpenAI] = None,
    ) -> list[dict]:
        """
        Translate VN keywords to EN for Pexels search.
        
        Args:
            keywords: List of Vietnamese keywords
            client: OpenAI client
            
        Returns:
            List of translations with pexels_query
        """
        if not keywords:
            return []

        if client is None:
            client = OpenAI()

        keywords_str = ', '.join(f'"{kw}"' for kw in keywords)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Bạn là chuyên gia tìm kiếm video stock.
Dịch các từ khóa tiếng Việt sang tiếng Anh và tạo query phù hợp cho Pexels.
Trả lời JSON array."""
                },
                {
                    "role": "user",
                    "content": f'Translate these Vietnamese keywords: [{keywords_str}]'
                }
            ],
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)
        return result.get('translations', [])

    def calculate_total_duration(self, scenes: list[dict]) -> dict:
        """
        Calculate total duration stats.
        
        Returns:
            dict with total_duration_seconds and scene_count
        """
        return {
            'total_duration_seconds': sum(s['duration_seconds'] for s in scenes),
            'scene_count': len(scenes),
        }
```

---

## Bước 2: Celery Task

**File:** `apps/worker/tasks/scene_breakdown.py`

```python
"""
Celery task for scene breakdown.
"""
from celery import Task
from apps.worker.celery_app import celery_app
from apps.worker.services.scene_breaker import SceneBreaker
from apps.worker.services.progress_tracker import ProgressTracker
from apps.worker.services.supabase_admin import get_supabase_admin
from openai import OpenAI
import json


@celery_app.task(
    name='apps.worker.tasks.scene_breakdown.run',
    bind=True,
    max_retries=1,
    acks_late=True,
)
def run(self: Task, job_id: str, script_data: dict, assistant_id: str) -> dict:
    """
    Break script into scenes with B-roll data.
    
    Args:
        job_id: Job UUID
        script_data: Script JSON from Task Group 3
        assistant_id: Channel assistant UUID
        
    Returns:
        dict with scenes array
    """
    supabase = get_supabase_admin()
    tracker = ProgressTracker(supabase, job_id)

    try:
        # === FETCH CHANNEL PACING ===
        tracker.start('fetch_pacing')

        assistant = supabase.table('channel_assistants').select('pacing_profile').eq('id', assistant_id).single().execute()
        pacing_wpm = assistant.data.get('pacing_profile', {}).get('wpm', 150) if assistant.data else 150

        tracker.done('fetch_pacing')

        # === SEGMENT SCENES ===
        tracker.start('segment_scenes')

        breaker = SceneBreaker(default_wpm=pacing_wpm)

        # Get script text
        script_text = script_data.get('body', script_data.get('script_text', ''))
        target_duration = script_data.get('estimated_duration_minutes', 10)

        scenes = breaker.segment_scenes(
            script_text=script_text,
            pacing_wpm=pacing_wpm,
            target_duration_minutes=target_duration,
        )

        tracker.done('segment_scenes')

        # === TRANSLATE B-ROLL KEYWORDS ===
        tracker.start('broll_translation')

        all_keywords = []
        for scene in scenes:
            all_keywords.extend(scene.get('broll_keywords', []))

        if all_keywords:
            openai = OpenAI()
            translations = await breaker.translate_broll_keywords(all_keywords, openai)

            # Map translations back to scenes
            translation_map = {t['vn']: t for t in translations}
            for scene in scenes:
                scene['broll_translations'] = [
                    translation_map[kw]
                    for kw in scene.get('broll_keywords', [])
                    if kw in translation_map
                ]
        else:
            for scene in scenes:
                scene['broll_translations'] = []

        tracker.done('broll_translation')

        # === SAVE RESULTS ===
        stats = breaker.calculate_total_duration(scenes)
        result = {
            'scenes': scenes,
            **stats,
        }

        supabase.table('jobs').update({
            'status': 'succeeded',
            'progress': 100,
            'result_payload': result,
            'sub_progress': tracker.get_sub_progress(),
        }).eq('id', job_id).execute()

        # Update generated_scripts with scenes
        supabase.table('generated_scripts').update({
            'scenes': scenes,
        }).eq('job_id', job_id).execute()

        return result

    except Exception as e:
        tracker.fail('scene_breakdown', str(e))
        supabase.table('jobs').update({
            'status': 'failed',
            'error_message': str(e),
        }).eq('id', job_id).execute()
        raise
```

---

## Bước 3: Update API Router

**File:** `apps/api/routers/scripts.py` (ADD this endpoint)

```python
@router.post('/breakdown-scenes', response_model=ScriptResponse)
async def breakdown_scenes(
    req: GenerateScriptRequest,
    user_id: str = Depends(get_supabase_user),
):
    """
    Trigger scene breakdown for latest generated script.
    """
    admin = get_supabase_admin()

    # Get latest script for this assistant
    existing_script = (
        admin.table('generated_scripts')
        .select('*')
        .eq('assistant_id', str(req.assistant_id))
        .order('created_at', desc=True)
        .limit(1)
        .execute()
    )

    if not existing_script.data:
        raise HTTPException(400, 'No script found. Generate a script first.')

    script_data = existing_script.data[0]
    script_json = json.loads(script_data['script_text'])

    # Create job
    job_result = admin.table('jobs').insert({
        'user_id': user_id,
        'task_type': 'scene_breakdown',
        'input_payload': {
            'assistant_id': str(req.assistant_id),
            'script_data': script_json,
        },
        'status': 'pending',
    }).execute()

    job = job_result.data[0]
    job_id = job['id']

    # Enqueue task
    from apps.worker.tasks.scene_breakdown import run as scene_breakdown_task
    task = scene_breakdown_task.delay(
        job_id=job_id,
        script_data=script_json,
        assistant_id=str(req.assistant_id),
    )

    admin.table('jobs').update({'celery_task_id': task.id}).eq('id', job_id).execute()

    return ScriptResponse(
        job_id=job_id,
        status='pending',
        message=f'Scene breakdown started. Track at /api/jobs/{job_id}',
    )
```

---

## Bước 4: Unit Tests

**File:** `apps/worker/services/test_scene_breaker.py`

```python
"""
Unit tests for SceneBreaker.
"""
import pytest
from apps.worker.services.scene_breaker import SceneBreaker


class TestSceneBreaker:
    """Test suite for SceneBreaker."""

    @pytest.fixture
    def breaker(self):
        return SceneBreaker(default_wpm=150)

    def test_segment_scenes_basic(self, breaker):
        """Test basic scene segmentation."""
        script = """Hook content here.

This is the body paragraph one.

This is body paragraph two.

CTA at the end."""

        scenes = breaker.segment_scenes(script, wpm=150)

        assert len(scenes) == 4
        assert scenes[0]['scene_number'] == 1
        assert scenes[0]['start_time'] == 0.0
        assert scenes[0]['text'] == "Hook content here."
        assert 'broll_keywords' in scenes[0]

    def test_segment_scenes_timestamps(self, breaker):
        """Test timestamp calculation."""
        script = "Word " * 300  # 300 words

        scenes = breaker.segment_scenes(script, wpm=150)
        # 300 words / 150 wpm = 2 minutes = 120 seconds

        assert len(scenes) == 1
        assert scenes[0]['duration_seconds'] == pytest.approx(120.0, rel=1)

    def test_extract_broll_keywords(self, breaker):
        """Test B-roll keyword extraction."""
        text = "Hôm nay tôi đang nấu ăn tại bếp với nguyên liệu tươi."

        keywords = breaker._extract_broll_keywords(text)

        assert 'nấu ăn' in keywords
        assert 'tại bếp' in keywords

    def test_extract_broll_keywords_empty(self, breaker):
        """Test extraction with no keywords."""
        text = "Đây là một câu không có từ khóa nào."

        keywords = breaker._extract_broll_keywords(text)

        assert len(keywords) == 0

    def test_calculate_total_duration(self, breaker):
        """Test duration calculation."""
        scenes = [
            {'duration_seconds': 60.0},
            {'duration_seconds': 90.0},
            {'duration_seconds': 45.0},
        ]

        stats = breaker.calculate_total_duration(scenes)

        assert stats['total_duration_seconds'] == 195.0
        assert stats['scene_count'] == 3
```

---

## Bước 5: Verify

```bash
cd apps/worker && pytest services/test_scene_breaker.py -v
```

---

## Commands for Tier 2

```bash
cat docs/plan/CONTEXT-sprint3-scene-breakdown.md
cat docs/plan/SKILL-ROUTING-sprint3-scene-breakdown.md
cat docs/plan/PLAN-sprint3-scene-breakdown.md
cat docs/plan/MSEW-sprint3-scene-breakdown.md
cat docs/plan/ACCEPTANCE-sprint3-scene-breakdown.md
```
