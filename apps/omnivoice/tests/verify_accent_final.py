html = open("app/templates/index.html", encoding="utf-8").read()

checks = [
    ("dropdown: khmer accent option",  'value="khmer accent"' in html),
    ("dropdown: burmese accent option", 'value="burmese accent"' in html),
    ("dropdown: Campuchia label",      'Campuchia - Khmer' in html),
    ("dropdown: Burmese label",        'Myanmar - Burmese' in html),
    ("dropdown: best-effort warning",  'best-effort' in html),
    ("dropdown: Voice Cloning hint",   '<strong>Voice Cloning</strong>' in html),
    ("preset: km has khmer accent",    'moderate pitch, khmer accent"' in html),
    ("preset: my has burmese accent",  'moderate pitch, burmese accent"' in html),
    ("backward: american kept",        'value="american accent"' in html),
    ("backward: chinese kept",         'value="chinese accent"' in html),
    ("backward: indian kept",          'value="indian accent"' in html),
    ("backward: 7 old accents count",  sum(f'value="{a}"' in html for a in
                                            ["american accent","british accent","australian accent",
                                             "chinese accent","japanese accent","korean accent",
                                             "indian accent"]) == 7),
]
all_pass = True
for name, ok in checks:
    print(f"  {'[OK]' if ok else '[FAIL]':6s} {name}")
    if not ok:
        all_pass = False
print()
print("PASSED" if all_pass else "FAILED")
exit(0 if all_pass else 1)