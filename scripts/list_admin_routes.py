"""List admin routes from FastAPI app, output format: METHOD|PATH"""
import os
import sys

# Ensure repo root on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.api.main import app

routes = sorted(set(
    (r.path, ','.join(sorted(r.methods or [])))
    for r in app.routes
    if hasattr(r, 'path') and '/admin' in r.path
))
for path, methods in routes:
    primary = methods.split(',')[0]
    print(f"{primary}|{path}")
