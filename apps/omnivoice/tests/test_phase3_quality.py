"""Phase 3 smoke test: verify /v1/version, request-id logging, version bump.

Khong can model that — test schema + endpoint behavior.
"""

import io
import logging
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent / "app"
sys.path.insert(0, str(APP_DIR))

import main as main_module
from fastapi.testclient import TestClient


# Mock model de test /v1/tts (can response 200)
def mock_generate(**kwargs):
    import numpy as np

    return [np.zeros(24000, dtype=np.float32)]


main_module.model = type(
    "M",
    (),
    {
        "generate": staticmethod(mock_generate),
        "config": type("C", (), {"samplerate": 24000})(),
    },
)()

client = TestClient(main_module.app)


# === CASE 1: /v1/version returns correct schema ===
print("=== CASE 1: GET /v1/version ===")
r = client.get("/v1/version")
print(f"status={r.status_code}")
assert r.status_code == 200
body = r.json()
print(f"  body keys: {sorted(body.keys())}")
expected_keys = {
    "server_version",
    "server_name",
    "omnivoice_version",
    "omnivoice_path",
    "omnivoice_pinned_tag",
    "model_loaded",
}
assert expected_keys.issubset(body.keys()), f"Missing keys: {expected_keys - body.keys()}"
print(f"  server_version={body['server_version']!r} (expect '1.1.0')")
print(f"  omnivoice_version={body['omnivoice_version']!r}")
print(f"  omnivoice_pinned_tag={body['omnivoice_pinned_tag']!r} (expect '0.2.0')")
print(f"  model_loaded={body['model_loaded']}")
assert body["server_version"] == "1.1.0"
assert body["omnivoice_pinned_tag"] == "0.2.0"
assert body["server_name"] == "omnivoice-api-server"
print("  [PASS]")


# === CASE 2: request-id appears in log output ===
print()
print("=== CASE 2: request-id logging trong /v1/tts ===")
log_stream = io.StringIO()
log_handler = logging.StreamHandler(log_stream)
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(logging.Formatter("%(asctime)sZ [%(levelname)s] %(name)s: %(message)s"))
root_logger = logging.getLogger()
root_logger.addHandler(log_handler)
try:
    r = client.post("/v1/tts", json={"text": "test request", "language": "vi"})
    print(f"status={r.status_code}")
    assert r.status_code == 200
    log_output = log_stream.getvalue()
    print(f"  log lines: {len(log_output.splitlines())}")
    # Tim it nhat 1 log line co [req=xxxxxxxxxxxx]
    req_id_matches = re.findall(r"\[req=[a-f0-9]{12}\]", log_output)
    print(f"  request-id markers found: {len(req_id_matches)}")
    print(f"  sample log line: {log_output.splitlines()[0][:100] if log_output else 'EMPTY'}")
    assert len(req_id_matches) >= 2, f"Expected >=2 request-id markers, got {len(req_id_matches)}"
    # Kiem tra logs co UTC suffix "Z"
    assert any("Z [" in line for line in log_output.splitlines()), "Logs phai co UTC suffix 'Z'"
    print("  [PASS] request-id va UTC format OK")
finally:
    root_logger.removeHandler(log_handler)


# === CASE 3: request-id unique giua 2 request ===
print()
print("=== CASE 3: request-id unique giua cac request ===")
log_stream2 = io.StringIO()
log_handler2 = logging.StreamHandler(log_stream2)
log_handler2.setLevel(logging.INFO)
log_handler2.setFormatter(logging.Formatter("%(message)s"))
root_logger.addHandler(log_handler2)
try:
    r1 = client.post("/v1/tts", json={"text": "request 1", "language": "vi"})
    r2 = client.post("/v1/tts", json={"text": "request 2", "language": "vi"})
    assert r1.status_code == 200 and r2.status_code == 200
    log_output = log_stream2.getvalue()
    req_ids = set(re.findall(r"\[req=([a-f0-9]{12})\]", log_output))
    print(f"  unique request-ids: {len(req_ids)}")
    assert len(req_ids) >= 2, f"Expected unique IDs, got {req_ids}"
    print("  [PASS]")
finally:
    root_logger.removeHandler(log_handler2)


# === CASE 4: Backward compat - Phase 2 pad/fade van hoat dong ===
print()
print("=== CASE 4: Phase 2 backward compat - pad/fade ===")
r = client.post("/v1/tts", json={"text": "test", "pad_duration": 0.2, "fade_duration": 0.1})
print(f"status={r.status_code}")
assert r.status_code == 200
print("  [PASS]")


# === CASE 5: All existing endpoints still work ===
print()
print("=== CASE 5: Backward compat - all endpoints ===")
endpoints = [
    ("GET", "/", 200),
    ("GET", "/health", 200),
    ("GET", "/v1/version", 200),
    ("GET", "/api/voices", 200),
]
for method, path, expected in endpoints:
    r = client.get(path)
    print(f"  {method} {path}: status={r.status_code}")
    assert r.status_code == expected, f"{method} {path} expected {expected}, got {r.status_code}"
print("  [PASS] All endpoints OK")


# === CASE 6: 422 validation (pad_duration < 0) — da fix trong Phase 2 ===
print()
print("=== CASE 6: Validation 422 (pad am khong bi 500) ===")
r = client.post("/v1/tts", json={"text": "test", "pad_duration": -0.1})
print(f"status={r.status_code}")
assert r.status_code == 422
print("  [PASS]")


print()
print("=== ALL 6 PHASE 3 TESTS PASSED ===")
