"""LLM-powered analysis using GPT-4o."""
import os
import json
from typing import List, Dict, Any
import openai
from apps.api.modules.llm.prompts import HOOK_ANALYSIS_PROMPT, EXTRACT_STRUCTURE_PROMPT, GENERATE_MIMIC_RULES_PROMPT

class LLMAnalyzer:
    """GPT-4o for analysis."""
    
    def __init__(self, api_key: str = None):
        self.client = openai.AsyncOpenAI(api_key=api_key or os.environ.get('OPENAI_API_KEY'))
    
    async def analyze_hooks(self, transcripts: List[str], titles: List[str] = None) -> dict:
        """Output 8: Hook Analysis."""
        if titles is None:
            titles = ["Unknown"] * len(transcripts)
            
        prompt = HOOK_ANALYSIS_PROMPT.format(
            titles=chr(10).join(titles[:10]),
            transcripts=chr(10).join([t[:200] for t in transcripts[:10]])
        )
        
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    
    async def extract_structure(self, transcripts: List[str]) -> dict:
        """Output 9: Structural Formula."""
        prompt = EXTRACT_STRUCTURE_PROMPT.format(
            transcripts=chr(10).join([t[:500] for t in transcripts[:5]])
        )
        
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    
    async def generate_mimic_rules(self, transcripts: List[str]) -> dict:
        """Output 11: Mimic Rules."""
        prompt = GENERATE_MIMIC_RULES_PROMPT.format(
            transcripts=chr(10).join([t[:500] for t in transcripts[:5]])
        )
        
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
