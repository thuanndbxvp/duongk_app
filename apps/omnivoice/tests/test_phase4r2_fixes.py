"""Phase 4R-ext: Verify UI fixes (dropdown bg + lang-select visible + save form)."""

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


# === FIX 1: Dropdown CSS ===
print()
print("=== FIX 1: Dropdown CSS (browser default highlight) ===")
# Verify select co custom arrow SVG + option styling
assert "appearance: none" in html, "Custom arrow CSS missing"
assert "background-image: url" in html and "svg" in html, "SVG arrow missing"
assert "select option" in html, "option styling missing"
assert "background-color: #1e1e2e" in html, "Option bg color missing"
print("  [PASS] Custom arrow + option styling present")


# === FIX 2: Lang-select visibility ===
print()
print("=== FIX 2: Lang-select visibility ===")
# Dem so lan xuat hien (phai la 1, da di chuyen)
# Chi dem lan xuat hien TRONG body HTML, khong ke string trong JS
# (script co getElementById('lang-select') nhung khong co id="lang-select" the html that)
import re

# Tim TAT CA id="lang-select" XUAT HIEN nhu 1 HTML attribute (khong phai trong string JS)
id_attrs = re.findall(r'<[^>]*id="lang-select"[^>]*>', html)
print(f'  id="lang-select" attribute count: {len(id_attrs)} (expect 1)')
for a in id_attrs:
    print(f"    {a[:80]}")
assert len(id_attrs) == 1, f"Expected exactly 1 <select id=lang-select>, got {len(id_attrs)}"
print("  [PASS] Chi co 1 lang-select trong body (script reference khong dem)")

# Kiem tra lang-select XUAT HIEN TRUOC cac mode-panel
panel_instruct_pos = html.index('id="panel-instruct"')
lang_pos = html.index('id="lang-select"')
print(f"  lang-select pos={lang_pos}")
print(f"  panel-instruct pos={panel_instruct_pos}")
assert lang_pos < panel_instruct_pos, "lang-select phai o TRUOC panel-instruct (da promote len)"
print("  [PASS] Lang-select da duoc promote len ngoai mode panels")

# Kiem tra co class global-setting + form-hint
assert 'class="form-group global-setting"' in html, "global-setting class missing"
assert "form-hint" in html, "form-hint small text missing"
assert "UI luôn tiếng Việt" in html, "Hint UI luon tieng Viet missing"
print("  [PASS] Global setting block co form-hint")


# === FIX 3: Save voice form ===
print()
print("=== FIX 3: Save voice to registry form ===")
assert 'id="save-voice-id"' in html, "save-voice-id input missing"
assert 'id="save-voice-name"' in html, "save-voice-name input missing"
assert 'id="save-voice-status"' in html, "save-voice-status element missing"
assert "saveVoiceToRegistry()" in html, "saveVoiceToRegistry function call missing"
assert "function saveVoiceToRegistry()" in html, "saveVoiceToRegistry function definition missing"
assert "btn-secondary" in html, "btn-secondary CSS class missing"
print("  [PASS] Save form co input + button + function")

# Kiem tra save block chi hien trong panel-instruct
panel_instruct_pos = html.index('id="panel-instruct"')
panel_clone_pos = html.index('id="panel-clone"')
save_pos = html.index('class="form-group save-voice-block"')
# save-block phai nam trong panel-instruct (truoc panel-clone)
print(f"  panel-instruct pos={panel_instruct_pos}")
print(f"  panel-clone pos={panel_clone_pos}")
print(f"  save-block pos={save_pos}")
assert panel_instruct_pos < save_pos < panel_clone_pos, "Save block phai o trong panel-instruct"
print("  [PASS] Save block o trong Voice Design panel (khong phai Clone)")


# === FIX 4: Khong con duplicate lang-select trong Advanced ===
print()
print("=== FIX 4: Khong con duplicate ===")
# Phai co comment "Lang-select da duoc chuyen len Global Settings"
assert "Lang-select da duoc chuyen len Global Settings" in html, "Migration comment missing"
print("  [PASS] Da xoa block cu trong Advanced, ghi chu migration")


# === FIX 5: Validate JS function ===
print()
print("=== FIX 5: saveVoiceToRegistry validation ===")
assert "voiceID phai la chu thuong + so + underscore" in html
assert "Instruct khong duoc rong" in html
assert "POST" in html  # method
assert "/v1/voices" in html  # endpoint
print("  [PASS] Validation + POST /v1/voices")


# === FIX 6: Design mode hien thi 8 lang options ===
print()
print("=== FIX 6: Dropdown van co 8 ngon ngu ===")
import re

m = re.search(r'<select id="lang-select"[^>]*>(.*?)</select>', html, re.DOTALL)
assert m
opts = re.findall(r'<option value="([^"]+)"', m.group(1))
print(f"  options: {opts}")
assert set(opts) == {"vi", "km", "my", "en", "zh", "es", "hi", "ar", "auto"}
print("  [PASS]")

print()
print("=== ALL FIXES VERIFIED ===")
