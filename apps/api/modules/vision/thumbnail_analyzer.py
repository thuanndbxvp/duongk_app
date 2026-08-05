"""GPT-4o Vision for thumbnail analysis."""
import os
import json
from typing import List
import openai

class ThumbnailAnalyzer:
    """GPT-4o Vision for thumbnails."""
    
    def __init__(self, api_key: str = None):
        self.client = openai.AsyncOpenAI(api_key=api_key or os.environ.get('OPENAI_API_KEY'))
    
    async def analyze_thumbnails(self, thumbnail_urls: List[str]) -> dict:
        """Output 14: Thumbnail Analysis."""
        if not thumbnail_urls:
            return {'avg_thumbnail_style': {}, 'thumbnail_effectiveness': {}}
        
        content = [{"type": "text", "text": "Analyze these YouTube thumbnails. Return JSON: {\"avg_thumbnail_style\": {\"text_presence\": true, \"face_presence\": true}, \"thumbnail_effectiveness\": {\"avg_ctr_correlation\": 0.5}}"}]
        
        for url in thumbnail_urls[:20]:
            content.append({"type": "image_url", "image_url": {"url": url}})
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": content}],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Vision API error: {e}")
            return {'avg_thumbnail_style': {}, 'thumbnail_effectiveness': {}}
