"""Phase 6 smoke test: VoiceID Registry + 5 endpoint don gian.

Test:
  1. GET /v1/identify (server info)
  2. GET /v1/catalog (list voice)
  3. GET /v1/voices/{id} (single voice)
  4. POST /v1/voices (upsert)
  5. POST /v1/voices/{id}/tts (TTS theo voiceID)
  6. DELETE /v1/voices/{id}
  7. Error cases (404 voice_not_found, 400 missing text, 422 invalid meta)
"""

import shutil
import sys
import tempfile
from pathlib import Path

# Tao temp registry file de khong ghi vao production data
TEMP_DIR = Path(tempfile.mkdtemp(prefix="phase6_test_"))
TEST_REGISTRY = TEMP_DIR / "voice_registry.json"
TEST_SERVER_ID = TEMP_DIR / "server_id.txt"

# Copy file goc vao temp de test co data thuc
ORIG_REGISTRY = Path(__file__).resolve().parent.parent / "voice_registry.json"
shutil.copy(ORIG_REGISTRY, TEST_REGISTRY)

# Patch path truoc khi import
APP_DIR = Path(__file__).resolve().parent.parent / "app"
sys.path.insert(0, str(APP_DIR))

import main as main_module

# Monkey-patch cac path trong main module de dung test files
from voice_registry import VoiceRegistry  # noqa: E402

main_module._REGISTRY_PATH = TEST_REGISTRY
main_module._SERVER_ID_PATH = TEST_SERVER_ID
main_module.registry = VoiceRegistry(TEST_REGISTRY)
# Force regenerate server_id
if TEST_SERVER_ID.exists():
    TEST_SERVER_ID.unlink()
main_module.SERVER_ID = main_module._get_or_create_server_id()
print(f"Test setup: registry={TEST_REGISTRY}")
print(f"Test setup: server_id={main_module.SERVER_ID}")


# Mock model
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

from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(main_module.app)


# === CASE 1: GET /v1/identify ===
print()
print("=== CASE 1: GET /v1/identify ===")
r = client.get("/v1/identify")
print(f"status={r.status_code}")
assert r.status_code == 200
body = r.json()
print(f"  keys: {sorted(body.keys())}")
expected_keys = {
    "server_id",
    "server_version",
    "server_name",
    "hostname",
    "ip_local",
    "port",
    "supported_languages",
    "omnivoice_version",
    "omnivoice_pinned_tag",
    "model_status",
    "voice_count",
}
assert expected_keys.issubset(body.keys()), f"Missing: {expected_keys - body.keys()}"
print(f"  server_id={body['server_id'][:16]}...")
print(f"  ip_local={body['ip_local']}")
print(f"  port={body['port']}")
print(f"  voice_count={body['voice_count']} (expect 11)")
assert body["voice_count"] == 11
assert body["supported_languages"] == ["vi", "km", "my", "en", "zh", "es", "hi", "ar"]
print("  [PASS]")


# === CASE 2: GET /v1/catalog (list 11 voices, KHONG co instruct) ===
print()
print("=== CASE 2: GET /v1/catalog ===")
r = client.get("/v1/catalog")
print(f"status={r.status_code}")
assert r.status_code == 200
body = r.json()
print(f"  count={body['count']}")
assert body["count"] == 11
assert len(body["voices"]) == 11
# Kiem tra KHONG co instruct (security)
first = body["voices"][0]
print(f"  first voice: {first['id']} type={first.get('type')}")
assert "instruct" not in first, "Catalog KHONG duoc tra instruct (security)"
# Phai co display_name, type, language
assert "display_name" in first
assert "type" in first
assert "language" in first
print("  [PASS] 11 voices, KHONG leak instruct")


# === CASE 3: GET /v1/voices/{id} (single + co instruct) ===
print()
print("=== CASE 3: GET /v1/voices/{id} ===")
r = client.get("/v1/voices/narrator_vi_male")
print(f"status={r.status_code}")
assert r.status_code == 200
body = r.json()
print(f"  id={body['id']} type={body['type']} language={body['language']}")
print(f"  display_name={body.get('display_name')!r}")
print(f"  instruct={'male' in body.get('instruct', '')}")
assert body["type"] == "design"
assert body["language"] == "vi"
assert "instruct" in body, "Single voice endpoint PHAI co instruct"
print("  [PASS]")


# === CASE 3b: Voice khong ton tai -> 404 ===
print()
print("=== CASE 3b: Voice not found -> 404 ===")
r = client.get("/v1/voices/this_voice_does_not_exist")
print(f"status={r.status_code}, detail={r.json().get('detail')}")
assert r.status_code == 404
assert r.json()["detail"]["code"] == "voice_not_found"
print("  [PASS]")


# === CASE 4: POST /v1/voices/{id}/tts ===
print()
print("=== CASE 4: POST /v1/voices/{id}/tts (design type) ===")
r = client.post("/v1/voices/narrator_vi_female/tts", json={"text": "Xin chao cac ban"})
print(f"status={r.status_code}, audio_size={len(r.content)}")
assert r.status_code == 200
assert r.headers.get("content-type") == "audio/wav"
assert r.content[:4] == b"RIFF"
print("  [PASS] audio/wav OK")


# === CASE 4b: tts voiceID khong ton tai -> 404 ===
print()
print("=== CASE 4b: tts voiceID not found -> 404 ===")
r = client.post("/v1/voices/no_such_voice/tts", json={"text": "hello"})
print(f"status={r.status_code}")
assert r.status_code == 404
print("  [PASS]")


# === CASE 4c: tts text rong -> 400 ===
print()
print("=== CASE 4c: tts text empty -> 400 ===")
r = client.post("/v1/voices/narrator_vi_female/tts", json={"text": "  "})
print(f"status={r.status_code}")
assert r.status_code == 400
print("  [PASS]")


# === CASE 4d: clone type (clone_my_voice) ===
print()
print("=== CASE 4d: tts clone type (clone_my_voice) ===")
r = client.post("/v1/voices/clone_my_voice/tts", json={"text": "Test clone voice"})
print(f"status={r.status_code}, audio_size={len(r.content)}")
assert r.status_code == 200
assert r.headers.get("content-type") == "audio/wav"
print("  [PASS] clone type OK")


# === CASE 4e: auto type (auto_random) ===
print()
print("=== CASE 4e: tts auto type (auto_random) ===")
r = client.post("/v1/voices/auto_random/tts", json={"text": "Test auto voice"})
print(f"status={r.status_code}, audio_size={len(r.content)}")
assert r.status_code == 200
print("  [PASS] auto type OK")


# === CASE 4f: tts with query param override (speed) ===
print()
print("=== CASE 4f: tts with speed query param ===")
r = client.post(
    "/v1/voices/narrator_vi_female/tts?speed=1.5",
    json={"text": "Fast speech"},
)
print(f"status={r.status_code}")
assert r.status_code == 200
print("  [PASS]")


# === CASE 5: POST /v1/voices (upsert) ===
print()
print("=== CASE 5: POST /v1/voices (upsert new) ===")
new_voice = {
    "id": "test_new_voice",
    "type": "design",
    "language": "en",
    "instruct": "male, elderly, low pitch",
    "display_name": "Test voice",
    "description": "Voice tao trong test",
}
r = client.post("/v1/voices", json=new_voice)
print(f"status={r.status_code}")
assert r.status_code == 200
body = r.json()
assert body["id"] == "test_new_voice"
assert body["type"] == "design"
print("  [PASS] upsert OK")
# Verify list now co 12 voices
r = client.get("/v1/catalog")
assert r.json()["count"] == 12, f"Expected 12 voices, got {r.json()['count']}"
print("  [PASS] catalog count = 12")


# === CASE 5b: upsert validation fail (type=design thieu instruct) ===
print()
print("=== CASE 5b: upsert invalid -> 422 ===")
r = client.post("/v1/voices", json={"id": "bad", "type": "design", "language": "vi"})
print(f"status={r.status_code}, detail={r.json().get('detail')}")
assert r.status_code == 422
assert r.json()["detail"]["code"] == "invalid_meta"
print("  [PASS]")


# === CASE 5c: upsert clone thieu ref_audio_file ===
print()
print("=== CASE 5c: upsert clone without ref_audio_file -> 422 ===")
r = client.post("/v1/voices", json={"id": "bad_clone", "type": "clone", "language": "vi"})
print(f"status={r.status_code}")
assert r.status_code == 422
print("  [PASS]")


# === CASE 6: DELETE /v1/voices/{id} ===
print()
print("=== CASE 6: DELETE voice ===")
r = client.delete("/v1/voices/test_new_voice")
print(f"status={r.status_code}")
assert r.status_code == 204
# Verify deleted
r = client.get("/v1/voices/test_new_voice")
assert r.status_code == 404
print("  [PASS] delete returns 204 + subsequent GET returns 404")


# === CASE 6b: DELETE khong ton tai -> 404 ===
print()
print("=== CASE 6b: DELETE non-existent -> 404 ===")
r = client.delete("/v1/voices/no_such_voice")
print(f"status={r.status_code}")
assert r.status_code == 404
print("  [PASS]")


# === CASE 7: Backward compat (cac endpoint cu) ===
print()
print("=== CASE 7: Backward compat - cac endpoint cu ===")
for path in ["/", "/health", "/v1/version", "/api/voices"]:
    r = client.get(path)
    assert r.status_code == 200, f"{path} fail"
    print(f"  GET {path}: 200 OK")
# POST /v1/tts van hoat dong (Phase 2 compat)
r = client.post("/v1/tts", json={"text": "test", "language": "vi"})
assert r.status_code == 200
print("  POST /v1/tts: 200 OK")
print("  [PASS]")


# Cleanup
shutil.rmtree(TEMP_DIR, ignore_errors=True)
print()
print("=== ALL 7 PHASE 6 TESTS PASSED ===")
