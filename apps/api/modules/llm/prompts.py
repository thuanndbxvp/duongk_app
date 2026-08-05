"""Prompt templates for LLM Analyzer."""

HOOK_ANALYSIS_PROMPT = """Analyze these video titles and transcripts to identify hook patterns.

Titles: {titles}

Transcripts (first 30s): {transcripts}

Return JSON: {{"hook_patterns": [{{"type": "string", "example": "string", "effectiveness_score": 0.0}}], "hook_framework": "string"}}"""


EXTRACT_STRUCTURE_PROMPT = """Analyze these transcripts to find the structural pattern.

Transcripts: {transcripts}

Return JSON: {{"typical_structure": {{"opening": {{"seconds": 15}}, "main_content": {{"seconds": 600}}}}, "structure_type": "string"}}"""


GENERATE_MIMIC_RULES_PROMPT = """Analyze these transcripts to create mimic rules.

Transcripts: {transcripts}

Return JSON: {{"mimic_guidelines": {{"vocabulary_level": "string", "common_phrases": ["string"]}}, "tone": "string"}}"""
