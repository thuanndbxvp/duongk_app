"""
Backend: GET /api/voices/providers — list supported TTS providers.
Hidden Features P3: Added for voice profile create form.
"""
PROVIDERS = [
    {
        "id": "omnivoice",
        "name": "OmniVoice",
        "languages": ["vi-VN", "en-US"],
        "supports_clone": True,
        "requires_sample": True,
        "max_sample_duration_sec": 60,
    },
    {
        "id": "elevenlabs",
        "name": "ElevenLabs",
        "languages": ["en-US", "en-GB", "ja-JP", "ko-KR"],
        "supports_clone": True,
        "requires_sample": True,
        "max_sample_duration_sec": 120,
    },
    {
        "id": "google_cloud_tts",
        "name": "Google Cloud TTS",
        "languages": ["vi-VN", "en-US", "en-GB", "ja-JP", "ko-KR", "zh-CN", "fr-FR"],
        "supports_clone": False,
        "requires_sample": False,
        "max_sample_duration_sec": 0,
    },
]


async def get_voice_providers():
    """Return list of supported voice providers."""
    return {"providers": PROVIDERS}
