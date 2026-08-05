"""
Custom OpenAPI Schema Configuration.

Adds metadata, tags, and custom info to auto-generated OpenAPI spec.
"""
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi_schema(app: FastAPI) -> dict:
    """
    Generate custom OpenAPI schema with additional metadata.
    
    Args:
        app: FastAPI application instance
    
    Returns:
        OpenAPI schema dictionary
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="YouTube AI SaaS API",
        version="1.0.0",
        description="""
## API Overview

This API provides YouTube content intelligence capabilities for automated video content creation.

### Modules

- **Module 1 - Niche Validate**: Validates YouTube niche viability using Google Trends
- **Module 2A - Deep Collection**: Collects video metadata from YouTube channels
- **Transcript Engine**: 3-tier transcript retrieval (YouTube API → Supadata → Whisper)

### Authentication

All endpoints require JWT Bearer token in the Authorization header (except `/health`).

### Rate Limits

- Anonymous: 10 requests/minute
- Authenticated: 100 requests/minute

### Errors

All errors return standard JSON format:

```json
{
  "detail": "Error message description"
}
```

### Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Internal Server Error |
""",
        routes=app.routes,
    )
    
    # Add custom info
    openapi_schema["info"]["contact"] = {
        "name": "API Support",
        "email": "api@appdk.vn",
        "url": "https://appdk.vn"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "Proprietary",
        "url": "https://appdk.vn/terms"
    }
    
    # Add servers
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Local Development"
        },
        {
            "url": "https://api.staging.appdk.vn",
            "description": "Staging"
        },
        {
            "url": "https://api.appdk.vn",
            "description": "Production"
        }
    ]
    
    # Add tags metadata
    openapi_schema["tags"] = [
        {
            "name": "Module 1 - Niche Validate",
            "description": "Validates YouTube niche viability"
        },
        {
            "name": "Module 2A - Deep Collection",
            "description": "Collects video metadata from YouTube channels"
        },
        {
            "name": "Transcript Engine",
            "description": "3-tier transcript retrieval"
        },
        {
            "name": "Documentation",
            "description": "API documentation endpoints"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema
