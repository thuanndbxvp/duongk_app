"""
Verify environment variables for AppDK development.
Run: python scripts/check-env.py
"""
import os
import sys
from pathlib import Path


# Load .env nếu có (optional — Tier 2 có thể chạy trước khi copy env)
ENV_FILE = Path(__file__).parent.parent / '.env'
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, _, value = line.partition('=')
            os.environ.setdefault(key.strip(), value.strip())


# Required vars + optional flag
VARS = [
    # (name, required, description)
    ('SUPABASE_URL', True, 'Project URL'),
    ('SUPABASE_ANON_KEY', True, 'Public anon key'),
    ('SUPABASE_SERVICE_ROLE_KEY', True, 'Server-side key'),
    ('SUPABASE_JWT_SECRET', True, 'JWT verification secret'),
    ('NEXT_PUBLIC_SUPABASE_URL', True, 'Mirror for Next.js'),
    ('NEXT_PUBLIC_SUPABASE_ANON_KEY', True, 'Mirror for Next.js'),
    ('REDIS_URL', True, 'Redis connection'),
    ('CELERY_BROKER_URL', True, 'Celery broker'),
    ('CELERY_RESULT_BACKEND', True, 'Celery result backend'),
    ('OPENAI_API_KEY', True, 'OpenAI GPT-4o, Whisper'),
    ('COHERE_API_KEY', True, 'Cohere Embed v3'),
    ('YOUTUBE_API_KEY_1', True, 'YouTube Data API v3'),
    ('SUPADATA_API_KEY', True, 'Tier 2 transcript fallback'),
    ('SERPAPI_KEY', True, 'Pytrends fallback'),
    ('R2_ACCESS_KEY_ID', True, 'Cloudflare R2 token'),
    ('R2_SECRET_ACCESS_KEY', True, 'Cloudflare R2 token secret'),
    ('R2_ENDPOINT', True, 'R2 endpoint URL'),
    ('R2_BUCKET_UPLOADS', True, 'R2 uploads bucket'),
    ('R2_BUCKET_RENDERS', True, 'R2 renders bucket'),
    ('R2_BUCKET_CACHE', True, 'R2 cache bucket'),
    ('R2_PUBLIC_CDN', True, 'R2 public CDN URL'),
    ('MODAL_TOKEN_ID', True, 'Modal auth token ID'),
    ('MODAL_TOKEN_SECRET', True, 'Modal auth token secret'),
    # Optional
    ('SENTRY_DSN', False, 'Error tracking (optional)'),
    ('ADMIN_ALLOWED_IPS', False, 'Admin IP whitelist (defaults to 127.0.0.1)'),
    ('STALI_API_KEY', False, 'Stali LLM (optional — unused)'),
    ('STALI_BASE_URL', False, 'Stali base URL (optional)'),
    ('PYTHONUNBUFFERED', False, 'Python log flush (set to 1)'),
    ('ENV', False, 'App environment (development/production)'),
    ('NODE_ENV', False, 'Node environment'),
]


def main() -> int:
    print('AppDK — Environment Check')
    print('=' * 70)
    print(f'{"Variable":<35} {"Status":<10} {"Description"}')
    print('-' * 70)
    
    missing_required = 0
    
    for name, required, description in VARS:
        value = os.environ.get(name)
        if value:
            # Mask secret keys (chỉ hiện prefix + ***)
            if any(k in name.upper() for k in ('KEY', 'SECRET', 'TOKEN', 'PASSWORD')):
                masked = value[:4] + '***' if len(value) > 4 else '***'
                status = f'[OK] {masked}'
            else:
                status = f'[OK] {value[:30]}'
        else:
            status = '[MISSING]' if required else '[OPTIONAL]'
            if required:
                missing_required += 1
        
        print(f'{name:<35} {status:<10} {description}')
    
    print('-' * 70)
    
    if missing_required == 0:
        print(f'\n✓ All {len(VARS)} variables checked. {sum(1 for _, r, _ in VARS if r)} required — all present.')
        return 0
    else:
        print(f'\n✗ {missing_required} required variable(s) MISSING.')
        print('  → Xem docs/ENV-VARS.md để biết cách lấy.')
        return 1


if __name__ == '__main__':
    sys.exit(main())