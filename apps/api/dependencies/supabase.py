"""
Supabase client dependencies.
"""
import os
from supabase import create_client, Client

def get_supabase_admin() -> Client:
    """Get Supabase client with service_role key for admin tasks."""
    url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL', 'https://xxx.supabase.co')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'xxx')
    return create_client(url, key)
