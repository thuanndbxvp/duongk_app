import pytest
from unittest.mock import AsyncMock, patch
from apps.api.modules.llm.analyzer import LLMAnalyzer
from apps.api.modules.vision.thumbnail_analyzer import ThumbnailAnalyzer

@pytest.mark.asyncio
async def test_llm_analyzer():
    with patch('openai.AsyncOpenAI') as mock_client:
        mock_chat_completion = AsyncMock()
        mock_client.return_value.chat.completions.create = mock_chat_completion
        mock_message = type('obj', (object,), {'content': '{"hook_patterns": [], "hook_framework": "test"}'})()
        mock_response = type('obj', (object,), {'choices': [type('obj', (object,), {'message': mock_message})()]})()
        mock_chat_completion.return_value = mock_response

        analyzer = LLMAnalyzer(api_key="test-key")
        result = await analyzer.analyze_hooks(["test"], ["test"])
        assert "hook_framework" in result

@pytest.mark.asyncio
async def test_vision_analyzer():
    with patch('openai.AsyncOpenAI') as mock_client:
        mock_chat_completion = AsyncMock()
        mock_client.return_value.chat.completions.create = mock_chat_completion
        mock_message = type('obj', (object,), {'content': '{"avg_thumbnail_style": {}, "thumbnail_effectiveness": {}}'})()
        mock_response = type('obj', (object,), {'choices': [type('obj', (object,), {'message': mock_message})()]})()
        mock_chat_completion.return_value = mock_response

        analyzer = ThumbnailAnalyzer(api_key="test-key")
        result = await analyzer.analyze_thumbnails(["http://example.com/img.jpg"])
        assert "avg_thumbnail_style" in result
