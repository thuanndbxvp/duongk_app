"""
Celery task for idea generation.
"""
from celery import Task
from apps.worker.celery_app import celery_app
from apps.worker.progress_tracker import ProgressTracker
from apps.worker.services.idea_generator import IdeaGenerator
from supabase import create_client
import os
import asyncio


@celery_app.task(
    name='apps.worker.tasks.idea_generate.run',
    bind=True,
    max_retries=2,
    acks_late=True,
)
def run(self: Task, job_id: str, assistant_id: str) -> dict:
    """
    Generate video topic ideas with gap analysis.
    
    Args:
        job_id: Job UUID
        assistant_id: Channel assistant UUID
        
    Returns:
        dict with ideas list
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
            # === FETCH DATA ===
            await tracker.start('fetch_data')

            assistant = supabase.table('channel_assistants').select('*').eq('id', assistant_id).single().execute()
            if not assistant.data:
                raise ValueError(f"Assistant {assistant_id} not found")

            analysis = supabase.table('channel_deep_analysis').select('*').eq('assistant_id', assistant_id).order('created_at', desc=True).limit(1).execute()
            if not analysis.data:
                raise ValueError(f"No analysis found for assistant {assistant_id}")

            metadata = analysis.data[0].get('metadata_report', {})
            tags = metadata.get('top_tags', [])[:20]
            if not tags:
                # Mock tags if empty
                tags = ["cách nấu ăn", "làm bánh", "ẩm thực", "review món ăn", "nấu ăn nhanh", "món ngon mỗi ngày"]
                
            channel_avg_views = metadata.get('avg_views', 50000)
            channel_total_views = metadata.get('total_views', 1000000)

            await tracker.complete('fetch_data', {"status": "done"})

            # === CLUSTER TOPICS ===
            await tracker.start('cluster_topics')

            generator = IdeaGenerator()
            clustered = generator.cluster_topics(tags, min_cluster_size=3)

            await tracker.complete('cluster_topics', {"status": "done"})

            # === CALCULATE GAP SCORES ===
            await tracker.start('gap_analysis')

            ideas = []
            for cluster_id in set(c['cluster_id'] for c in clustered):
                if cluster_id == -1:  # Skip noise
                    continue

                cluster_topics = [c['topic'] for c in clustered if c['cluster_id'] == cluster_id]
                cluster_label = cluster_topics[0] if cluster_topics else "misc"
                
                # find cluster label from clustered
                for c in clustered:
                    if c['cluster_id'] == cluster_id:
                        cluster_label = c['cluster_label']
                        break

                # Mock trending score (would come from Google Trends API)
                trending_score = 50.0

                gap_score = generator.calculate_gap_score(
                    topic=cluster_label,
                    channel_views=channel_total_views,
                    channel_avg_views=channel_avg_views,
                    niche_trending=trending_score,
                )

                ideas.append({
                    'idea_topic': cluster_label,
                    'gap_score': gap_score,
                    'cluster_id': cluster_id,
                    'related_topics': cluster_topics[:5],
                    'opportunity_description': generator.generate_opportunity_description(cluster_label, gap_score),
                    'confidence': generator.assign_confidence(gap_score),
                })

            # Sort by gap score
            ideas.sort(key=lambda x: x['gap_score'], reverse=True)

            await tracker.complete('gap_analysis', {"status": "done"})

            # === SAVE RESULTS ===
            result = {
                'ideas': ideas,
                'total_ideas': len(ideas),
                'top_opportunities': ideas[:5],
            }

            supabase.table('jobs').update({
                'status': 'completed',
                'progress': 100,
                'result_payload': result,
                'sub_progress': tracker._cache,
            }).eq('id', job_id).execute()

            # Save ideas to database
            for idea in ideas:
                supabase.table('generated_ideas').insert({
                    'job_id': job_id,
                    'assistant_id': assistant_id,
                    'idea_topic': idea['idea_topic'],
                    'gap_score': idea['gap_score'],
                    'cluster_id': idea['cluster_id'],
                    'opportunity_description': idea['opportunity_description'],
                    'confidence': idea['confidence'],
                }).execute()

            return result

        except Exception as e:
            await tracker.fail('idea_generate', str(e))
            supabase.table('jobs').update({
                'status': 'failed',
                'error_message': str(e),
            }).eq('id', job_id).execute()
            raise
            
    return asyncio.run(_run())
