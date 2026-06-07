#!/usr/bin/env python3
"""Rebrand pass §1/§2/§8: textual brand tokens in index.html + data bundle.
Shader -> BZN15. Reversible (backups *.bak_rebrand exist). Re-runnable.
Does NOT touch portfolio §7 (Norrköpings Symfoniorkester/Hamn, client copy),
images/SVG/GLB, prismic OG slug, or Umami id (handled in later passes)."""
import re, sys, os

ROOT = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(ROOT, "mirror_root", "index.html")
BUNDLE = os.path.join(ROOT, "mirror_root", "_next", "static", "chunks", "09d2g3rtnbzgs.js")

# Ordered literal replacements (longest / most-specific brand phrases first).
REPL = [
    # --- studio name + legal entity (before generic "Shader") ---
    ("Shader Development Studio", "BZN15"),
    ("Shader Sweden AB",          "BZN15 s.r.l."),
    ("Shader Sweden",             "BZN15"),                 # alternateName 2nd elem
    # --- emails (before domain rename; they contain shader.se) ---
    ("hello@shader.se",     "info@bzn15.it"),
    ("ceo@shader.se",       "ceo@bzn15.it"),
    ("secretary@shader.se", "segretaria@bzn15.it"),
    # --- company address (targeted; NOT a global Norrköping/Sweden replace) ---
    ("Laxholmstorget 3",       "Lungomare Starita 62"),
    ("602 21",                 "70132"),
    ("Norrköping, Sweden",     "Bari, Italy"),              # foundingLocation (both copies)
    ("Norrköping<br/>Sweden",  "Bari (BA)<br/>Italy"),      # visible <address>
    ('country:"Sweden"',       'country:"Italy"'),          # bundle address obj
    # country code SE -> IT (rendered / escaped / bundle)
    ('addressCountry":"SE"',     'addressCountry":"IT"'),
    ('addressCountry\\":\\"SE\\"','addressCountry\\":\\"IT\\"'),
    ('countryCode:"SE"',         'countryCode:"IT"'),
    # --- positioning copy: drop "Sweden" HQ claim ---
    ("Based in Sweden", "Based in Italy"),
    # --- ids / booking / social ---
    ("5593233140",          "IT09016880727"),               # taxID / P.IVA
    ("simon-hedlund-kglzne","bzn15"),                        # Cal.com slug (PLACEHOLDER)
    ("shadersweden",        "bzn15"),                        # social handle (PLACEHOLDER)
    # --- generic brand token (AFTER all phrases above) ---
    ("Shader", "BZN15"),                                     # case-sensitive
    # --- domain (AFTER emails) ---
    ("shader.se", "bzn15.it"),
]

# JSON-LD addressLocality value, escaping-agnostic: "Norrköping" only when it
# closes a JSON string (next char is a quote or backslash). Portfolio uses
# "Norrköpings ..." (followed by 's') -> NOT matched.
LOCALITY_RE = (re.compile(r'Norrköping(?=[\\"])'), "Bari")

TECH = ("vertexShader", "fragmentShader", "ShaderMaterial", "useShader")

def load(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def save(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)

def process(path, label):
    data = load(path)
    # SAFETY: refuse to run if a technical GLSL "Shader" token is present here.
    tech_hit = [t for t in TECH if t in data]
    if tech_hit:
        print(f"!! ABORT {label}: technical shader token(s) present: {tech_hit}")
        sys.exit(2)
    print(f"\n===== {label} ({os.path.basename(path)}) =====")
    for old, new in REPL:
        n = data.count(old)
        if n:
            data = data.replace(old, new)
            print(f"  {n:>3}x  {old!r} -> {new!r}")
    n = len(LOCALITY_RE[0].findall(data))
    if n:
        data = LOCALITY_RE[0].sub(LOCALITY_RE[1], data)
        print(f"  {n:>3}x  /Norrköping(?=[\\\\\"])/ -> {LOCALITY_RE[1]!r}")
    save(path, data)
    return data

def audit(path, label):
    data = load(path)
    print(f"\n----- AUDIT leftovers: {label} -----")
    for t in ("Shader", "shader.se", "shadersweden", "5593233140",
              "Laxholmstorget", "simon-hedlund", "hello@shader", "Norrköping", "Sweden"):
        c = data.count(t)
        flag = "  <-- expected 0" if t in (
            "Shader","shader.se","shadersweden","5593233140",
            "Laxholmstorget","simon-hedlund","hello@shader") and c else ""
        print(f"  {c:>3}x  {t}{flag}")
    # show remaining Norrköping / Sweden contexts so we can confirm they're portfolio
    for m in re.finditer(r'Norrköping|Sweden', data):
        s = max(0, m.start()-45); e = min(len(data), m.end()+25)
        print("     ·", data[s:e].replace("\n", " "))

for p, lbl in ((HTML, "index.html"), (BUNDLE, "bundle")):
    process(p, lbl)
for p, lbl in ((HTML, "index.html"), (BUNDLE, "bundle")):
    audit(p, lbl)
print("\nDONE.")
