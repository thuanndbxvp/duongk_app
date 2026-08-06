from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import sentry_sdk
import os
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()

# OpenAPI custom schema
from apps.api.openapi import custom_openapi_schema

# Import routers
from apps.api.modules.module_1 import router as module_1_router
from apps.api.modules.module_2a import router as module_2a_router
from apps.api.modules.transcript.routes import router as transcript_router
from apps.api.modules.analysis.routes import router as analysis_router
from apps.api.modules.nlp.routes import router as nlp_router
from apps.api.modules.llm.routes import router as llm_router
from apps.api.modules.rag.routes import router as rag_router
from apps.api.modules.script.routes import router as script_router
from apps.api.routers.users import router as user_router
from apps.api.routers.credits import router as credits_router
from apps.api.routers.projects import router as projects_router
from apps.api.modules.voice.routes import router as voice_router

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))
app = FastAPI(title="YouTube AI SaaS")

# Include routers
app.include_router(module_1_router)
app.include_router(module_2a_router)
app.include_router(transcript_router)
app.include_router(analysis_router)
app.include_router(nlp_router)
app.include_router(llm_router)
app.include_router(rag_router)
app.include_router(script_router)
app.include_router(user_router)
app.include_router(credits_router)
app.include_router(projects_router)
app.include_router(voice_router)

# Override default OpenAPI schema
app.openapi = lambda: custom_openapi_schema(app)

@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API docs."""
    return RedirectResponse(url="/docs")


@app.get("/openapi.json", include_in_schema=False)
async def openapi_json():
    """Return raw OpenAPI spec as JSON."""
    return app.openapi()


@app.get("/redoc", include_in_schema=False)
async def redoc():
    """Redirect to ReDoc documentation."""
    return RedirectResponse(url="/docs")