"""
Scene Breaker Service - Segment script into scenes with B-roll data.
"""
import re
import json
from typing import Optional
from openai import OpenAI


BROLL_PATTERNS = [
    (r'đang\s+(\S+(?:\s+\S+)?)', 'doing'),
    (r'(tại\s+\S+)', 'location'),
    (r'(nấu\s+\S+)', 'cooking'),
    (r'làm\s+(\S+(?:\s+\S+)?)', 'making'),
    (r'(cho\s+\S+\s+ăn)', 'food_prep'),
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
                    "content": "Bạn là chuyên gia tìm kiếm video stock.\nDịch các từ khóa tiếng Việt sang tiếng Anh và tạo query phù hợp cho Pexels.\nTrả lời JSON array với object: {'vn': 'từ khóa gốc', 'en': 'từ khóa dịch'}"
                },
                {
                    "role": "user",
                    "content": f'Translate these Vietnamese keywords: [{keywords_str}]'
                }
            ],
            response_format={"type": "json_object"},
        )

        try:
            result = json.loads(response.choices[0].message.content)
            # handle case where LLM returns {"translations": [...]} or just a list directly mapped to a key.
            # Updated system prompt requests a JSON array, but response_format={"type": "json_object"} requires an object.
            # Assuming {"translations": [{"vn": "...", "en": "..."}]}
            return result.get('translations', [])
        except Exception:
            return []

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
