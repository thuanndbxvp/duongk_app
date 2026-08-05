"""
Integration tests for RLS enforcement.
"""
import pytest
import uuid
from unittest.mock import patch


class TestRLS:
    """Test Row Level Security."""
    
    def test_user_can_see_own_jobs(self, user_client, admin_client):
        user_id = str(uuid.uuid4())
        client = user_client(user_id)
        
        # Create job for user
        admin_client.table('users').insert({
            'id': user_id,
            'email': 'test@example.com',
            'credits': 100,
        }).execute()
        
        job = admin_client.table('jobs').insert({
            'user_id': user_id,
            'task_type': 'collect_channel',
            'status': 'pending',
        }).execute()
        
        # User queries jobs
        result = client.table('jobs').select('*').eq('id', job.data[0]['id']).execute()
        assert len(result.data) == 1
    
    def test_user_cannot_see_other_users_jobs(self, user_client, admin_client):
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        
        # Create both users
        for uid in [user1_id, user2_id]:
            admin_client.table('users').insert({
                'id': uid,
                'email': f'{uid}@example.com',
                'credits': 100,
            }).execute()
        
        # User1 creates job
        job = admin_client.table('jobs').insert({
            'user_id': user1_id,
            'task_type': 'collect_channel',
            'status': 'pending',
        }).execute()
        job_id = job.data[0]['id']
        
        # User2 queries jobs - should NOT see user1's job
        user2_client = user_client(user2_id)
        result = user2_client.table('jobs').select('*').execute()
        
        # Verify user1's job is NOT in user2's results
        job_ids = [j['id'] for j in result.data]
        assert job_id not in job_ids
    
    def test_user_cannot_update_other_users_data(self, user_client, admin_client):
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        
        # Create user1
        admin_client.table('users').insert({
            'id': user1_id,
            'email': 'user1@example.com',
            'credits': 100,
        }).execute()
        
        # User2 tries to update user1's profile
        user2_client = user_client(user2_id)
        result = user2_client.table('users').update({'full_name': 'Hacker'}).eq('id', user1_id).execute()
        
        # Should not affect user1
        user1 = admin_client.table('users').select('*').eq('id', user1_id).single().execute()
        assert user1.data.get('full_name') != 'Hacker'
