"""RAG Storage using Supabase."""
from typing import List, Dict, Any
from supabase import create_client, Client
import os

class RAGStorage:
    def __init__(self):
        supabase_url = os.environ.get("SUPABASE_URL", "")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
    def store_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Store embedded chunks into dna_chunks table.
        chunks is a list of dicts with:
        - assistant_id
        - source_video_id
        - section
        - chunk_index
        - text_content
        - word_count
        - timestamp_start_sec
        - timestamp_end_sec
        - embedding
        - embedding_model
        """
        if not chunks:
            return
            
        # Bulk insert
        try:
            res = self.supabase.table("dna_chunks").insert(chunks).execute()
            return res.data
        except Exception as e:
            print(f"Error storing chunks: {e}")
            raise e
