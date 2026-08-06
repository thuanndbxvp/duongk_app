"""
Celery task for script generation with RAG + Anti-Slop.
"""
from celery import Task
from apps.worker.celery_app import celery_app
from apps.worker.services.rag_service import RAGService
from apps.api.modules.rag.embedder import Embedder
from apps.worker.services.antislop_service import AntiSlopService
from apps.worker.progress_tracker import ProgressTracker
from supabase import create_client
from openai import OpenAI
import json
import os
import asyncio
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from apps.api.services.routing import get_routing_config
from apps.worker.services.project_context import build_project_context


DEFAULT_BUDGET_USD = 0.10


def select_llm_provider() -> str:
    """Chọn LLM provider từ routing config. Fallback 'openai'."""
    routing = get_routing_config('llm_text')
    primary = routing.get('primary_provider')
    if primary and routing.get('enabled_providers', {}).get(primary, False):
        return primary
    return 'openai'  # fallback cứng


@celery_app.task(
    name='apps.worker.tasks.script_generate.run',
    bind=True,
    max_retries=2,
    acks_late=True,
)
def run(self: Task, job_id: str, assistant_id: str, topic: str) -> dict:
    """Generate script with RAG context and anti-slop validation."""
    supabase = create_client(
        os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co'),
        os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    )
    tracker = ProgressTracker(
        job_id=job_id,
        supabase_url=os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co'),
        supabase_key=os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    )

    async def _run():
        try:
            # === PHASE 1: RAG Retrieval (30%) ===
            await tracker.start('rag_retrieve')
            await tracker.increment('rag_retrieve', 10)

            embedder = Embedder()
            rag_service = RAGService(supabase, embedder)

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
            await tracker.increment('rag_retrieve', 30)

            # Build prompt
            prompt = rag_service.build_script_prompt(
                channel_persona=channel_persona,
                rag_context=context_result['context_text'],
                topic=topic,
            )
            await tracker.complete('rag_retrieve', {"status": "done"})

            # === PHASE 2: Generate Script (50%) ===
            await tracker.start('generate')
            await tracker.increment('generate', 10)

            # Phase 9 wire: select LLM provider từ routing
            provider = select_llm_provider()
            openai = OpenAI()

            if provider == 'openai':
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                )
            elif provider == 'stali':
                # Phase 10+ implement stali, fallback OpenAI
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                )
            else:
                # fallback cứng
                response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )

            script_data = json.loads(response.choices[0].message.content)
            await tracker.increment('generate', 40)

            # === PHASE 3: Anti-Slop Validation (20%) ===
            await tracker.start('validate')

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

            await tracker.complete('validate', {"status": "done"})
            await tracker.complete('generate', {"status": "done"})

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
                'status': 'completed',
                'progress': 100,
                'result_payload': result,
                'sub_progress': tracker._cache,
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
            await tracker.fail('generate', str(e))
            supabase.table('jobs').update({
                'status': 'failed',
                'error_message': str(e),
            }).eq('id', job_id).execute()
            raise
            
    return asyncio.run(_run())
@celery_app.task(
    name='apps.worker.tasks.script_generate.run_with_project',
    bind=True,
    max_retries=2,
    acks_late=True,
)
def run_with_project(self: Task, job_id: str, project_id: str, topic: str, assistant_id: str = "") -> dict:
    """
    Generate script using project context (Phase 01+).
    
    Uses build_project_context() to pull brief + optional channel DNA,
    falling back to blank mode when channel_assistant_id is null.
    The old assistant_id param is kept as fallback/wrapper.
    """
    supabase = create_client(
        os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co'),
        os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    )
    tracker = ProgressTracker(
        job_id=job_id,
        supabase_url=os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co'),
        supabase_key=os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    )

    async def _run():
        try:
            await tracker.start('rag_retrieve')
            await tracker.increment('rag_retrieve', 10)

            embedder = Embedder()
            rag_service = RAGService(supabase, embedder)

            # Build project context (new Phase 01 flow)
            ctx = await build_project_context(
                supabase=supabase,
                project_id=project_id,
                rag_service=rag_service,
                query=topic,
            )

            channel_persona = ctx.channel_dna or {}
            if not channel_persona and assistant_id:
                # Fallback: old flow with assistant_id
                assistant = supabase.table('channel_assistants').select('*').eq('id', assistant_id).single().execute()
                channel_persona = assistant.data.get('persona', {}) if assistant.data else {}

            # RAG context: use from project_context or fallback
            rag_context = ctx.rag_context
            if not rag_context and assistant_id:
                context_result = await rag_service.retrieve_context(
                    assistant_id=assistant_id,
                    query=topic,
                    top_k=10,
                    lambda_mmr=0.7,
                )
                rag_context = context_result['context_text']

            await tracker.increment('rag_retrieve', 30)

            # Build prompt
            prompt = rag_service.build_script_prompt(
                channel_persona=channel_persona,
                rag_context=rag_context,
                topic=topic,
            )
            await tracker.complete('rag_retrieve', {"status": "done"})

            # === PHASE 2: Generate Script ===
            await tracker.start('generate')
            await tracker.increment('generate', 10)

            provider = select_llm_provider()
            openai = OpenAI()

            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )

            script_data = json.loads(response.choices[0].message.content)
            await tracker.increment('generate', 40)

            # === PHASE 3: Anti-Slop Validation ===
            await tracker.start('validate')

            antislop = AntiSlopService()
            validation = antislop.validate_with_retry(
                script_text=script_data.get('body', ''),
                client=openai,
                max_retries=3,
                min_score=6.0,
                budget_usd=DEFAULT_BUDGET_USD,
            )

            script_data['mimic_score'] = validation['score']
            if validation['status'] != 'passed':
                script_data['validation_warning'] = validation['status']

            await tracker.complete('validate', {"status": "done"})
            await tracker.complete('generate', {"status": "done"})

            # === SAVE RESULTS ===
            result = {
                'script': script_data,
                'validation': {
                    'status': validation['status'],
                    'score': validation['score'],
                    'attempts': validation['attempts'],
                    'cost_usd': validation['total_cost'],
                },
            }

            supabase.table('jobs').update({
                'status': 'completed',
                'progress': 100,
                'result_payload': result,
                'sub_progress': tracker._cache,
            }).eq('id', job_id).execute()

            supabase.table('generated_scripts').insert({
                'job_id': job_id,
                'assistant_id': assistant_id or None,
                'topic': topic,
                'script_text': json.dumps(script_data),
                'score': validation['score'],
                'cost_usd': validation['total_cost'],
                'attempts': validation['attempts'],
            }).execute()

            return result

        except Exception as e:
            await tracker.fail('generate', str(e))
            supabase.table('jobs').update({
                'status': 'failed',
                'error_message': str(e),
            }).eq('id', job_id).execute()
            raise

    return asyncio.run(_run())

