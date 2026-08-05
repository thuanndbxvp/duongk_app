"""Phase 4R.4: API tab UI (Phase 6.6 - 1 muc con PARTIAL cua plan).

Kiem tra 3 tab nav + panel-api (4 sections) + JS loader + copy helpers.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
import main as main_module

main_module.model = type(
    "M",
    (),
    {
        "generate": staticmethod(lambda **kw: []),
        "config": type("C", (), {"samplerate": 24000})(),
    },
)()

from fastapi.testclient import TestClient

client = TestClient(main_module.app)

r = client.get("/")
assert r.status_code == 200
html = r.content.decode("utf-8")
print(f"HTML length: {len(html)} chars")


# === TEST 1: 3 tab nav buttons ===
print()
print("=== TEST 1: 3 tab buttons (Design + Clone + API) ===")
import re

tabs = re.findall(r'<button class="tab-btn[^"]*" id="tab-btn-(\w+)"[^>]*>', html)
print(f"  found {len(tabs)} tabs: {tabs}")
assert set(tabs) == {"instruct", "clone", "api"}, "Expected 3 tabs"
assert len(tabs) == 3, "Must have exactly 3 tabs"
print("  [PASS]")


# === TEST 2: panel-api exists ===
print()
print("=== TEST 2: panel-api HTML structure ===")
assert 'id="panel-api"' in html
assert 'class="mode-panel" id="panel-api"' in html, "panel-api phai co class mode-panel"
# Phai co 4 sections A/B/C/D (theo plan)
assert "A. Server Endpoint" in html, "Section A missing"
assert "B. VoiceID" in html, "Section B missing"
assert "C. Code mẫu" in html, "Section C missing"
assert "D. Quy trình" in html, "Section D missing"
print("  [PASS] 4 sections (A/B/C/D)")


# === TEST 3: Section A — server endpoint input + copy ===
print()
print("=== TEST 3: Section A — IP:port display ===")
assert 'id="api-server-url"' in html
assert 'id="api-server-hint"' in html
assert "copyToClipboard(" in html, "copyToClipboard fn call missing"
assert "GET /v1/identify" in html or "/v1/identify" in html
print("  [PASS]")


# === TEST 4: Section B — voice list grid ===
print()
print("=== TEST 4: Section B — VoiceID list ===")
assert 'id="api-voice-list"' in html
assert "api-voice-grid" in html, "CSS class api-voice-grid missing"
assert "api-voice-card" in html, "CSS class api-voice-card missing"
assert "copy-mini" in html, "copy-mini button class missing"
assert "copyText(" in html, "copyText fn call missing"
print("  [PASS]")


# === TEST 5: Section C — 4 code snippets (curl/Python/JS/Swift) ===
print()
print("=== TEST 5: Section C — 4 code snippets ===")
snippets = re.findall(r'id="snippet-(\w+)"', html)
print(f"  snippet ids: {snippets}")
assert set(snippets) == {"curl", "python", "js", "swift"}, f"Expected 4 snippets, got {snippets}"
assert len(snippets) == 4
# Each snippet phai co copy button (4 call site)
copy_snippet_calls = len(re.findall(r"onclick=\"copySnippet\(", html))
print(f"  copySnippet calls (as onclick): {copy_snippet_calls}")
assert copy_snippet_calls == 4
# CSS
assert ".snippet-card" in html
assert ".snippet-code" in html
assert ".snippet-header" in html
print("  [PASS]")


# === TEST 6: Section D — workflow 4 buoc ===
print()
print("=== TEST 6: Section D — workflow 4 buoc ===")
assert "Bước" in html or "buoc" in html or "Quy trình" in html
# Khong can check text cu the, chi can co the <ol>
assert "<ol" in html, "Ordered list missing"
assert "POST" in html and "/v1/voices/" in html
print("  [PASS]")


# === TEST 7: JS — switchMode('api') + loadApiTab() ===
print()
print("=== TEST 7: JS switchMode + loadApiTab ===")
assert "function switchMode(mode)" in html
assert "switchMode('api')" in html
assert "function loadApiTab()" in html
assert "loadApiTab();" in html, "switchMode phai call loadApiTab khi mode=api"
# Lazy load flag
assert "apiTabLoaded = true" in html
assert "apiServerUrl" in html
assert "apiSampleVoiceId" in html
print("  [PASS]")


# === TEST 8: JS — 4 snippet content templates ===
print()
print("=== TEST 8: 4 snippet templates ===")
assert "renderSnippets()" in html
assert "getElementById('snippet-curl')" in html
assert "getElementById('snippet-python')" in html
assert "getElementById('snippet-js')" in html
assert "getElementById('snippet-swift')" in html
assert "import requests" in html
assert "URLSession.shared" in html
assert "URL.createObjectURL" in html
assert "requests.post" in html or "requests\\.post" in html
print("  [PASS]")


# === TEST 9: Live — goi /v1/identify + /v1/catalog, verify contract ===
print()
print("=== TEST 9: Live contract check ===")
r = client.get("/v1/identify")
assert r.status_code == 200
info = r.json()
print(
    f"  /v1/identify: ip={info['ip_local']}, voices={info['voice_count']}, model={info['model_status']}"
)
assert info["model_status"] == "ready"
assert info["voice_count"] == 11

r = client.get("/v1/catalog")
assert r.status_code == 200
cat = r.json()
print(f"  /v1/catalog: {cat['count']} voices")
assert cat["count"] == 11
# Phai co 'id' field cho moi voice (UI dung no cho copy)
for v in cat["voices"]:
    assert "id" in v and v["id"], f"Voice missing id: {v}"
print("  [PASS] All voices have id field for UI to copy")


# === TEST 10: CSS classes for API tab ===
print()
print("=== TEST 10: CSS check ===")
required_classes = [
    ".api-section",
    ".api-endpoint-row",
    ".api-voice-grid",
    ".api-voice-card",
    ".snippet-card",
    ".snippet-code",
    ".snippet-header",
    ".btn-icon-secondary",
    ".snippet-lang",
]
for cls in required_classes:
    assert cls in html, f"CSS class {cls} missing"
print(f"  [PASS] {len(required_classes)} CSS classes")

print()
print("=== ALL PHASE 4R.4 (API TAB) TESTS PASSED ===")
