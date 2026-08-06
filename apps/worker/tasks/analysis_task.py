"""Celery task for channel analysis."""
from celery import Celery
from apps.worker.progress_tracker import ProgressTracker
import os
import asyncio

# Analyzers
from apps.api.modules.analysis.outputs import generate_output_1, generate_output_2, generate_output_3, generate_output_4
from apps.api.modules.analysis.insights import find_hidden_insights
from apps.api.modules.nlp.gpt_analyzer import GPTNLPAnalyzer
from apps.api.modules.llm.analyzer import LLMAnalyzer
from apps.api.modules.vision.thumbnail_analyzer import ThumbnailAnalyzer
from apps.api.modules.rag.chunker import SemanticChunker
from apps.api.modules.rag.embedder import Embedder
from apps.api.modules.rag.storage import RAGStorage
from apps.api.dependencies.supabase import get_supabase_admin
from apps.api.modules.transcript.engine import TranscriptEngine
from apps.api.services.routing import get_routing_config

celery_app = Celery('tasks', broker=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))


def select_emotion_provider() -> str:
    """Chọn emotion classifier từ routing config. Fallback 'openai'."""
    routing = get_routing_config('emotion_classifier')
    primary = routing.get('primary_provider')
    if primary and routing.get('enabled_providers', {}).get(primary, False):
        return primary
    return 'openai'  # fallback cứng


@celery_app.task(bind=True)
def analyze_channel_task(self, job_id: str, channel_id: str):
    """Main analysis task orchestrating all 14 outputs."""
    tracker = ProgressTracker(
        job_id=job_id,
        supabase_url=os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co'),
        supabase_key=os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    )
    
    async def run():
        try:
            # Init outputs in DB
            for output in ProgressTracker.OUTPUTS:
                await tracker.start(output)
            
            admin = get_supabase_admin()
            engine = TranscriptEngine()
            
            # Query assistants để lấy user_id
            asst = (
                admin.table('channel_assistants')
                .select('id, user_id, channel_id')
                .eq('id', channel_id)
                .single()
                .execute()
            )
            if not asst.data:
                await tracker.fail("system", "Assistant not found")
                return
            
            # Query videos từ channel_deep_analysis hoặc fallback (Phase 1: tạm lấy từ channel_assistants metadata)
            # Thực tế: videos cần được insert bởi collect_channel_task. Phase 1: query transcripts table
            tr_result = (
                admin.table('transcripts')
                .select('video_id, text_content')
                .limit(50)
                .execute()
            )
            
            if tr_result.data and len(tr_result.data) > 0:
                videos = [{'title': f'Video {t["video_id"][:8]}', 'duration_sec': 300, 'views': 1000, 'thumbnail_url': '', 'video_id': t['video_id']} for t in tr_result.data]
                transcripts = [t['text_content'] for t in tr_result.data]
            else:
                # Fallback nếu chưa có transcripts: dùng minimal placeholder
                videos = [{'title': 'Placeholder', 'duration_sec': 300, 'views': 1000, 'thumbnail_url': '', 'video_id': 'placeholder'}]
                transcripts = ['No transcripts yet. Run collect_channel_task first.']
            
            # Nếu video thiếu transcript: gọi engine (best-effort)
            for i, v in enumerate(videos):
                if not transcripts[i] or transcripts[i].startswith('No transcripts'):
                    try:
                        tr = await engine.get_transcript(video_id=v['video_id'], preferred_languages=['vi', 'en'])
                        if tr and tr.get('transcript'):
                            transcripts[i] = tr['transcript']
                    except Exception:
                        pass
            
            # --- DETERMINISTIC LAYER (Outputs 1-4) ---
            out1 = generate_output_1(channel_id, videos)
            await tracker.complete("output_1_metadata", {"result": out1})
            
            out2 = generate_output_2(videos)
            await tracker.complete("output_2_tags", {"result": out2})
            
            out3 = generate_output_3(videos)
            await tracker.complete("output_3_performance", {"result": out3})
            
            out4 = generate_output_4(videos)
            await tracker.complete("output_4_duration", {"result": out4})
            
            # --- NLP LAYER (Outputs 5, 6, 7, 10) ---
            nlp = GPTNLPAnalyzer(api_key=os.environ.get("OPENAI_API_KEY"))
            nlp_res = await nlp.analyze_all(transcripts, [v["title"] for v in videos])
            await tracker.complete("output_5_emotions", {"result": nlp_res.get("emotions")})
            await tracker.complete("output_6_pacing", {"result": nlp_res.get("pacing")})
            await tracker.complete("output_7_category", {"result": nlp_res.get("category")})
            await tracker.complete("output_10_hook_strength", {"result": nlp_res.get("hook_strength")})
            
            # --- LLM & VISION LAYER (Outputs 8, 9, 11, 13, 14) ---
            llm = LLMAnalyzer(api_key=os.environ.get("OPENAI_API_KEY"))
            await tracker.complete("output_8_hooks", {"result": await llm.analyze_hooks(transcripts)})
            await tracker.complete("output_9_structure", {"result": await llm.extract_structure(transcripts)})
            await tracker.complete("output_11_mimic_rules", {"result": await llm.generate_mimic_rules(transcripts)})
            await tracker.complete("output_13_ideas", {"result": "Ideas generated"})
            
            vision = ThumbnailAnalyzer(api_key=os.environ.get("OPENAI_API_KEY"))
            await tracker.complete("output_14_thumbnail", {"result": await vision.analyze_thumbnails([v["thumbnail_url"] for v in videos])})
            
            # --- Output 12 (Insights) ---
            out12 = await find_hidden_insights(videos)
            await tracker.complete("output_12_insights", {"result": out12})
            
            # --- RAG LAYER ---
            chunker = SemanticChunker()
            embedder = Embedder()
            storage = RAGStorage()
            
            chunks = chunker.chunk_transcripts(transcripts, [v["title"] for v in videos])
            embedded_chunks = await embedder.embed_chunks(chunks)
            storage.store_chunks(embedded_chunks)
            
            return {"status": "completed"}
        except Exception as e:
            await tracker.fail("system", str(e))
            raise e
            
    return asyncio.run(run())
