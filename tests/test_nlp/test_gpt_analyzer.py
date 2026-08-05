"""Test GPT NLP Analyzer."""
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_analyze_all():
    """Test GPT-4o analysis."""
    with patch('openai.AsyncOpenAI') as mock_client:
        
        # Setup deep mock for OpenAI client
        mock_chat_completion = AsyncMock()
        mock_client.return_value.chat.completions.create = mock_chat_completion
        
        # Setup fake return value matching JSON structure
        mock_message = type('obj', (object,), {'content': '{"emotions": {}, "pacing": {}, "category": {}, "hooks": {}}'})()
        mock_choice = type('obj', (object,), {'message': mock_message})()
        mock_response = type('obj', (object,), {'choices': [mock_choice]})()
        
        mock_chat_completion.return_value = mock_response

        from apps.api.modules.nlp.gpt_analyzer import GPTNLPAnalyzer
        analyzer = GPTNLPAnalyzer(api_key="test-key")
        result = await analyzer.analyze_all(["test transcript"], ["Test Title"])

        assert 'emotions' in result or 'pacing' in result
