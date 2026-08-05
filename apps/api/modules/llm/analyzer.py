"""LLM-powered analysis using GPT-4o."""
import os
import json
from typing import List, Dict, Any
import openai

class LLMAnalyzer:
    """GPT-4o for analysis."""
    
    def __init__(self, api_key: str = None):
        self.client = openai.AsyncOpenAI(api_key=api_key or os.environ.get('OPENAI_API_KEY'))
    
    async def analyze_hooks(self, transcripts: List[str], titles: List[str]) -> dict:
        """Output 8: Hook Analysis."""
        prompt = f"""Analyze these video titles and transcripts to identify hook patterns.
        
Titles: {chr(10).join(titles[:10])}
        
Transcripts (first 30s): {chr(10).join([t[:200] for t in transcripts[:10]])}
        
Return JSON: {{"hook_patterns": [{{"type": "string", "example": "string", "effectiveness_score": 0.0}}], "hook_framework": "string"}}"""
        
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    
    async def extract_structure(self, transcripts: List[str]) -> dict:
        """Output 9: Structural Formula."""
        prompt = f"""Analyze these transcripts to find the structural pattern.
        
Transcripts: {chr(10).join([t[:500] for t in transcripts[:5]])}
        
Return JSON: {{"typical_structure": {{"opening": {{"seconds": 15}}, "main_content": {{"seconds": 600}}}}, "structure_type": "string"}}"""
        
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    
    async def generate_mimic_rules(self, transcripts: List[str]) -> dict:
        """Output 11: Mimic Rules."""
        prompt = f"""Analyze these transcripts to create mimic rules.
        
Transcripts: {chr(10).join([t[:500] for t in transcripts[:5]])}
        
Return JSON: {{"mimic_guidelines": {{"vocabulary_level": "string", "common_phrases": ["string"]}}, "tone": "string"}}"""
        
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
