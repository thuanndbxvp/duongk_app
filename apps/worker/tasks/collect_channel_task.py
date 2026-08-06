"""
Celery task: collect YouTube channel videos + transcripts.
Gọi YouTubeCollector + TranscriptEngine, insert vào DB.
"""
import os
import asyncio
from celery import Celery
from apps.api.modules.module_2a.service import YouTubeCollector
from apps.api.modules.transcript.engine import TranscriptEngine
from apps.api.dependencies.supabase import get_supabase_admin


celery_app = Celery('tasks', broker=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))


@celery_app.task(bind=True)
def collect_channel_task(self, assistant_id: str, channel_id: str):
    """
    Collect videos của channel + fetch transcripts.
    
    Args:
        assistant_id: UUID channel_assistants.id.
        channel_id: YouTube channel ID (UC...).
    """
    async def run():
        admin = get_supabase_admin()
        collector = YouTubeCollector()
        engine = TranscriptEngine()
        
        try:
            # Update status
            admin.table('channel_assistants').update({
                'status': 'collecting_videos',
            }).eq('id', assistant_id).execute()
            
            # Collect videos
            result = await collector.collect_channel_videos(
                channel_id=channel_id,
                max_videos=50,
            )
            quality_videos = result.get('quality_videos', [])
            
            # Insert videos (bảng videos table — nếu có, hoặc dùng channel_deep_analysis.metadata)
            # Tạm thời lưu vào raw_data của channel_assistants
            admin.table('channel_assistants').update({
                'status': 'fetching_transcripts',
                'updated_at': 'now()',
            }).eq('id', assistant_id).execute()
            
            # Fetch transcripts cho từng video (best-effort, max 10 để không timeout)
            transcripts_inserted = 0
            for video in quality_videos[:10]:
                video_id = video['id']
                try:
                    tr = await engine.get_transcript(
                        video_id=video_id,
                        preferred_languages=['vi', 'en'],
                    )
                    if tr and tr.get('transcript'):
                        admin.table('transcripts').upsert({
                            'video_id': video_id,
                            'text_content': tr['transcript'][:5000],
                            'raw_data': tr,
                            'fetched_at': 'now()',
                        }, on_conflict='video_id').execute()
                        transcripts_inserted += 1
                except Exception:
                    pass  # skip video nếu fail transcript
            
            # Update final status
            admin.table('channel_assistants').update({
                'status': 'ready',
                'updated_at': 'now()',
            }).eq('id', assistant_id).execute()
            
            return {
                'videos_collected': len(quality_videos),
                'transcripts_inserted': transcripts_inserted,
            }
        except Exception as e:
            admin.table('channel_assistants').update({
                'status': 'failed',
                'updated_at': 'now()',
            }).eq('id', assistant_id).execute()
            raise e
    
    return asyncio.run(run())