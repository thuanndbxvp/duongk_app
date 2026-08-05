"""
Anti-Slop Service - Validates scripts against AI slop patterns.
Layer 1: Regex (fast), Layer 2: LLM (slow), Layer 3: Cost cap retry.
"""
import re
import json
from typing import Optional
from openai import OpenAI


VIETNAMESE_SLOP_PATTERNS = [
    r'\b(cảm ơn bạn đã xem|like and subscribe|nhấn like|đăng ký kênh)\b',
    r'\b(chắc chắn|rất nhiều|một cách|tất cả các)\s+\w+\s+\w+\b',
    r'\b(xin vui lòng|đừng quên|hãy nhớ rằng)\b',
    r'\b(tuy nhiên|ngoài ra|mặt khác)\b',
]

ENGLISH_SLOP_PATTERNS = [
    r'\b(game-changer|leverage|synergy|scalable|paradigm|pivot|deep-dive)\b',
    r'\b(in this video|welcome back|let me know in comments)\b',
]


class AntiSlopService:
    """Service for detecting and filtering AI slop in scripts."""

    def __init__(self):
        self.vn_patterns = [re.compile(p, re.IGNORECASE) for p in VIETNAMESE_SLOP_PATTERNS]
        self.en_patterns = [re.compile(p, re.IGNORECASE) for p in ENGLISH_SLOP_PATTERNS]
        self.filler_pattern = re.compile(r'\b(um+|uh+|à|ừ|ờ|ơ|ạ)\b', re.IGNORECASE)

    def layer1_regex_check(self, text: str) -> tuple[bool, list[str]]:
        """
        Layer 1: Fast regex check for known slop patterns.
        
        Returns:
            (is_clean, violations)
        """
        violations = []

        # Vietnamese slop
        for pattern in self.vn_patterns:
            matches = pattern.findall(text)
            if matches:
                violations.append(f"VN slop: {matches[0]}")

        # English slop (shouldn't appear in Vietnamese script)
        for pattern in self.en_patterns:
            matches = pattern.findall(text)
            if matches:
                violations.append(f"EN slop: {matches[0]}")

        # Excessive fillers
        fillers = self.filler_pattern.findall(text)
        if len(fillers) > 5:
            violations.append(f"Too many fillers: {len(fillers)}")

        return len(violations) == 0, violations

    def layer2_llm_semantic_check(
        self,
        text: str,
        client: Optional[OpenAI] = None,
        model: str = "gpt-4o-mini",
    ) -> tuple[float, str]:
        """
        Layer 2: LLM semantic scoring.
        
        Returns:
            (score 1-10, reason)
        """
        if client is None:
            client = OpenAI()

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Bạn là chuyên gia đánh giá kịch bản YouTube tiếng Việt.\nĐánh giá dựa trên:\n1. Tính tự nhiên (không robotic, không văn mẫu)\n2. Độ độc đáo (không generic)\n3. Phù hợp văn hóa Việt Nam\n4. Không có filler words thái quá\n\nTrả lời JSON: {\"score\": 1-10, \"reason\": \"giải thích ngắn\"}"
                },
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)
        return float(result.get('score', 0)), result.get('reason', '')

    def validate_with_retry(
        self,
        script_text: str,
        client: Optional[OpenAI] = None,
        max_retries: int = 3,
        min_score: float = 6.0,
        budget_usd: float = 0.10,
    ) -> dict:
        """
        Layer 3: Cost-capped retry with best-of-N selection.
        
        Args:
            script_text: The script to validate
            client: OpenAI client
            max_retries: Maximum validation attempts
            min_score: Minimum passing score
            budget_usd: Maximum budget for validation
            
        Returns:
            dict with validation results
        """
        if client is None:
            client = OpenAI()

        best_result = {
            'text': script_text,
            'score': 0.0,
            'attempts': 1,
            'total_cost': 0.0,
            'status': 'initial',
            'reason': '',
        }

        # Layer 1 quick check
        is_clean, violations = self.layer1_regex_check(script_text)
        if not is_clean:
            best_result['status'] = 'layer1_failed'
            best_result['violations'] = violations
            return best_result

        for attempt in range(1, max_retries + 1):
            # Estimate cost
            estimated_cost = len(script_text) / 1000 * 0.0005

            # Check budget
            if best_result['total_cost'] + estimated_cost > budget_usd:
                best_result['status'] = 'budget_exceeded'
                break

            # LLM scoring
            score, reason = self.layer2_llm_semantic_check(script_text, client)

            # Track actual cost (rough estimate)
            actual_cost = estimated_cost * 1.2
            best_result['total_cost'] += actual_cost
            best_result['attempts'] = attempt
            best_result['reason'] = reason

            if score >= min_score:
                best_result['score'] = score
                best_result['status'] = 'passed'
                return best_result

            # Track best attempt
            if score > best_result['score']:
                best_result['score'] = score
                best_result['text'] = script_text

        best_result['status'] = 'max_retries_exhausted'
        return best_result
