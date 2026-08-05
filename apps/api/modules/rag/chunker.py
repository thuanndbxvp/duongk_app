"""Semantic chunking for transcripts."""
import re
from typing import List

class SemanticChunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, transcript: str) -> List[dict]:
        """Split transcript into semantic chunks."""
        sentences = re.split(r'[.!?]+', transcript)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks, current, current_tokens, chunk_start = [], [], 0, 0
        
        for sentence in sentences:
            tokens = len(sentence.split())
            if current_tokens + tokens > self.chunk_size:
                if current:
                    chunks.append({'text': ' '.join(current), 'start': chunk_start, 'end': chunk_start + current_tokens})
                # Overlap
                overlap_tokens, overlap_sents = 0, []
                for s in reversed(current):
                    t = len(s.split())
                    if overlap_tokens + t <= self.overlap:
                        overlap_sents.insert(0, s)
                        overlap_tokens += t
                    else: break
                current = overlap_sents + [sentence]
                current_tokens = overlap_tokens + tokens
                chunk_start += current_tokens - overlap_tokens - tokens
            else:
                current.append(sentence)
                current_tokens += tokens
        
        if current:
            chunks.append({'text': ' '.join(current), 'start': chunk_start, 'end': chunk_start + current_tokens})
        
        return chunks
