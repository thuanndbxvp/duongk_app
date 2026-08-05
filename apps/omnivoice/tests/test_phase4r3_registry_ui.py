"""Phase 4R.3: Verify Voice Registry UI manager."""

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


# === TEST 1: Registry block trong Design panel ===
print("=== TEST 1: Registry block UI ===")
assert 'class="form-group registry-block"' in html, "registry-block missing"
assert 'id="voice-registry-list"' in html, "voice-registry-list div missing"
assert "Voice Registry đã lưu" in html, "Vietnamese label missing"
print("  [PASS]")


# === TEST 2: Bang co header + cac cot ===
print()
print("=== TEST 2: Registry table CSS ===")
assert ".registry-table" in html, "table CSS missing"
assert ".registry-block code" in html, "code style missing"
assert ".btn-icon-danger" in html, "danger button CSS missing"
assert "thien" in html.lower() or "th{font" in html or "<th>" in html, "table header missing"
print("  [PASS]")


# === TEST 3: JS functions ===
print()
print("=== TEST 3: JS load + delete ===")
assert "function loadVoiceRegistry()" in html, "loadVoiceRegistry function missing"
assert "function deleteVoiceFromRegistry(" in html, "deleteVoiceFromRegistry missing"
assert "function escapeHtml(s)" in html, "escapeHtml XSS helper missing"
assert "function escapeAttr(s)" in html, "escapeAttr XSS helper missing"
assert "fetch(`${serverUrl}/v1/catalog`)" in html, "catalog fetch missing"
print("  [PASS]")


# === TEST 4: Auto-load khi page open ===
print()
print("=== TEST 4: Auto-load ===")
assert "loadVoiceRegistry();" in html
# Phai co trong init script (o cuoi file, sau checkHealth + loadVoices)
init_section = html[html.rfind("checkHealth();") :]
assert "loadVoiceRegistry()" in init_section, "loadVoiceRegistry phai o init block"
print("  [PASS]")


# === TEST 5: Confirm dialog cho xoa ===
print()
print("=== TEST 5: UX safety ===")
assert "confirm(" in html, "Confirm dialog missing for delete"
assert "Xoá voiceID" in html or "Xoa voiceID" in html, "Vietnamese confirm text missing"
assert "alert(" in html, "Error alert missing"
print("  [PASS]")


# === TEST 6: Auto-refresh sau khi save ===
print()
print("=== TEST 6: Auto-refresh after save ===")
# Tim phan "status = ok" trong saveVoice -> phai goi loadVoiceRegistry()
m_start = html.index("function saveVoiceToRegistry()")
m_end = html.index("function loadVoiceRegistry", m_start)
save_block = html[m_start:m_end]
print(f"  save block size: {len(save_block)} chars")
assert "loadVoiceRegistry()" in save_block, "save phai auto-refresh list"
assert "[OK] Da luu" in save_block, "Success message missing"
print("  [PASS] Auto-refresh after save")


# === TEST 7: Kiem tra API endpoint /v1/catalog contract ===
print()
print("=== TEST 7: Backend catalog endpoint ===")
r = client.get("/v1/catalog")
assert r.status_code == 200
body = r.json()
print(f"  count={body['count']} voices")
assert body["count"] == 11, "Expected 11 sample voices"
assert len(body["voices"]) == 11
# UI se render cac voice co id, type, language, display_name
first = body["voices"][0]
print(f"  sample: {first['id']} type={first['type']} lang={first['language']}")
print("  [PASS]")

print()
print("=== ALL REGISTRY UI TESTS PASSED ===")
