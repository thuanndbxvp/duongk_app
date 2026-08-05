"""Phase 4R smoke test: verify HTML structure after dropdown + slider additions.

Test:
  1. / GET / returns HTML containing 8 lang options
  2. Slider pad-range + fade-range co mat trong DOM
  3. onLanguageChange + LANGUAGE_PRESETS co trong script
  4. Payload builder (trong code) chua pad_duration + fade_duration
  5. No i18n files added (UI van tieng Viet)
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
import main as main_module
from fastapi.testclient import TestClient

main_module.model = type(
    "M",
    (),
    {
        "generate": staticmethod(lambda **kw: []),
        "config": type("C", (), {"samplerate": 24000})(),
    },
)()

client = TestClient(main_module.app)

# === CASE 1: GET / returns HTML, lay content ===
print("=== CASE 1: GET / returns HTML ===")
r = client.get("/")
print(f"status={r.status_code}, len={len(r.content)}")
assert r.status_code == 200
html = r.content.decode("utf-8")
assert "OmniVoice TTS Playground" in html
print("  [PASS]")


# === CASE 2: Dropdown ngon ngu co 8 option (vi/km/my/en/zh/es/hi/ar + auto) ===
print()
print("=== CASE 2: Dropdown co 8 ngon ngu ===")
# Lay phan <select id="lang-select">...</select>
m = re.search(
    r'<select id="lang-select"[^>]*>(.*?)</select>',
    html,
    re.DOTALL,
)
assert m, "Khong tim thay <select id='lang-select'>"
select_block = m.group(1)
opts = re.findall(r'<option value="([^"]+)"', select_block)
print(f"  options found: {opts}")
expected = {"vi", "km", "my", "en", "zh", "es", "hi", "ar", "auto"}
found = set(opts)
assert found == expected, f"Expected {expected}, got {found}"
print("  [PASS] All 9 options present (8 lang + auto)")


# === CASE 3: 2 slider pad/fade co mat ===
print()
print("=== CASE 3: Slider pad_duration + fade_duration co mat ===")
assert 'id="pad-range"' in html, "pad-range slider missing"
assert 'id="fade-range"' in html, "fade-range slider missing"
assert 'id="pad-val"' in html
assert 'id="fade-val"' in html
# Default values
pad_m = re.search(r'id="pad-range"[^>]*\svalue="([^"]+)"', html)
fade_m = re.search(r'id="fade-range"[^>]*\svalue="([^"]+)"', html)
print(f"  pad-range default: {pad_m.group(1) if pad_m else 'N/A'} (expect 0.15)")
print(f"  fade-range default: {fade_m.group(1) if fade_m else 'N/A'} (expect 0.05)")
assert pad_m and float(pad_m.group(1)) == 0.15
assert fade_m and float(fade_m.group(1)) == 0.05
print("  [PASS] Sliders present with correct defaults")


# === CASE 4: onchange handler cho lang-select ===
print()
print("=== CASE 4: lang-select co onchange handler ===")
assert 'id="lang-select"' in html
m = re.search(r'<select id="lang-select"[^>]*>', html)
select_tag = m.group(0)
print(f"  select tag: ...{select_tag[-60:]}")
assert "onchange=" in select_tag, "lang-select thieu onchange"
assert "onLanguageChange" in select_tag
print("  [PASS]")


# === CASE 5: LANGUAGE_PRESETS dict co 8 preset ===
print()
print("=== CASE 5: LANGUAGE_PRESETS dict co 8 preset ===")
m = re.search(r"const LANGUAGE_PRESETS\s*=\s*\{([^}]+)\}", html, re.DOTALL)
assert m, "LANGUAGE_PRESETS khong co trong script"
block = m.group(1)
keys = re.findall(r"^\s*(\w+):", block, re.MULTILINE)
print(f"  preset keys: {keys}")
expected_keys = {"vi", "km", "my", "en", "zh", "es", "hi", "ar"}
assert set(keys) == expected_keys, f"Expected {expected_keys}, got {set(keys)}"
# Kiem tra co accent cho en/zh/hi (theo plan)
assert "american accent" in block, "en preset thieu 'american accent'"
assert "chinese accent" in block, "zh preset thieu 'chinese accent'"
assert "indian accent" in block, "hi preset thieu 'indian accent'"
# ar phai co male (theo plan)
ar_m = re.search(r"ar:\s*\"([^\"]+)\"", block)
assert ar_m and "male" in ar_m.group(1), (
    f"ar preset phai co 'male', got: {ar_m.group(1) if ar_m else 'NOT FOUND'}"
)
print("  [PASS] 8 presets present with correct accents")


# === CASE 6: Payload builder chua pad_duration + fade_duration ===
print()
print("=== CASE 6: Payload builder truyen pad/fade ===")
# Match chinh xac: payload block bat dau bang "text: text," (cu the cua TTS payload, khong phai saveVoice)
m = re.search(
    r"const payload = \{\s*text: text,\s*\n([\s\S]*?pad_duration[\s\S]*?fade_duration[\s\S]*?)\};",
    html,
)
assert m, "Payload builder (TTS-specific) not found"
payload_block = "text: text, " + m.group(1)
payload_fields = [f.strip() for f in payload_block.split(chr(10)) if ":" in f][:12]
print(f"  payload fields: {payload_fields}")
assert "pad_duration" in payload_block
assert "fade_duration" in payload_block
assert "language" in payload_block
print("  [PASS]")


# === CASE 7: UI van tieng Viet (khong co i18n.js, khong co RTL Arabic) ===
print()
print("=== CASE 7: UI van tieng Viet, KHONG co i18n/RTL ===")
# Kiem tra khong co file i18n.js duoc include
assert "i18n.js" not in html, "Phase 4R khong dung i18n.js — UI phai 1 ngon ngu"
# Kiem tra khong co direction=rtl trong the html
html_tag_m = re.search(r"<html[^>]*>", html)
html_tag = html_tag_m.group(0)
print(f"  html tag: {html_tag}")
assert "dir=" not in html_tag or 'dir="ltr"' in html_tag, "Khong duoc co RTL Arabic"
# Kiem tra <html lang="vi"> (default Vietnamese)
assert 'lang="vi"' in html_tag, "UI phai mac dinh tieng Viet"
print("  [PASS] UI tieng Viet, khong i18n, khong RTL")


# === CASE 8: cac label tieng Viet con nguyen ===
print()
print("=== CASE 8: UI text van tieng Viet ===")
vietnamese_strings = [
    "BẮT ĐẦU CHUYỂN GIỌNG NÓI",
    "Thiết kế giọng (Voice Design)",
    "Clone giọng mẫu (Voice Cloning)",
    "Ngôn ngữ thuyết minh",
    "Tốc độ nói (Speed)",
    "Lặng pad đầu/cuối",
]
for s in vietnamese_strings:
    assert s in html, f"Missing Vietnamese string: {s!r}"
print(f"  [PASS] All {len(vietnamese_strings)} Vietnamese strings present")


print()
print("=== ALL 8 PHASE 4R TESTS PASSED ===")
