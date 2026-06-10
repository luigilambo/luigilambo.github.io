#!/usr/bin/env python3
"""Mirror the /work/<slug> project pages from shader.se into the local mirror.

Phase 1 — faithful local mirror (NO rebrand yet):
  - downloads each prerendered project page HTML
  - downloads any missing _next chunk referenced by them
  - rewrites only the host references needed for local independence:
        https://www.shader.se/      -> /            (self links, og, api/mux-image, /work)
        https://www.shader.se       -> /
        https://stream.mux.com/     -> /mux/         (JSON-LD contentUrl)
        https://analytics.shader.build/script.js -> /_a/script.js (no-op)
        https://analytics.shader.build           -> /_a
  - leaves external client links (gamilyapp.com, *.vercel.app, …) untouched
  - writes  mirror_root/work/<slug>/index.html  (+ index.html.orig raw copy)

Videos: every project mux_playback_id is already present in mirror_root/mux/,
so the patched app chunk builds /mux/<id>.m3u8 with no extra download.
"""
import os, re, sys, urllib.request

BASE   = "https://www.shader.se"
HERE   = os.path.dirname(os.path.abspath(__file__))
ROOT   = os.path.join(HERE, "mirror_root")
CHUNKS = os.path.join(ROOT, "_next", "static", "chunks")

# Solo gli 8 servizi mantenuti dopo il rebrand BZN15. I 3 rimossi
# (design-is-funny, heip, norrkopings-hamn) NON vanno re-fetchati: li
# ricreerebbe come pagine Shader, mai rebrandizzate.
SLUGS = [
    "alamance-foods", "ehealth-arena", "gamily", "glasbolaget",
    "ica-nissen", "select-concept", "son", "spp-dream-generator",
]

UA = {"User-Agent": "Mozilla/5.0 (mirror-tool)"}

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def rewrite(html: str) -> str:
    # IMPORTANT: the RSC flight stream (self.__next_f) uses byte-length-prefixed
    # rows ("<id>:T<hexlen>,<text>"). Any length change inside those rows shifts
    # the byte offsets and crashes the React flight parser
    # ("t.reason.enqueueModel is not a function"). So the host rewrite below MUST
    # be length-preserving:  https://www.shader.se  (21) -> http://127.0.0.1:8300 (21).
    assert len("https://www.shader.se") == len("http://127.0.0.1:8300")
    html = html.replace("https://www.shader.se", "http://127.0.0.1:8300")

    # analytics lives only in the static <head> (<link preload>) and __next_s,
    # NOT in the flight stream -> safe to shorten to the local no-op.
    html = html.replace("https://analytics.shader.build/script.js", "/_a/script.js")
    html = html.replace("https://analytics.shader.build", "/_a")

    # stream.mux.com is left untouched on purpose: it only appears inside JSON-LD
    # "contentUrl" (incl. flight rows) as SEO metadata — never fetched — and
    # shortening it would corrupt the length-prefixed rows. Playback uses the
    # mux_playback_id field, which the patched app chunk turns into /mux/<id>.m3u8.
    return html

def ensure_chunks(html: str):
    """Download any referenced _next chunk we don't have locally."""
    refs = set(re.findall(r"_next/static/chunks/[A-Za-z0-9_.~-]+\.(?:js|css)", html))
    for ref in sorted(refs):
        dest = os.path.join(ROOT, ref)
        if os.path.isfile(dest):
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        data = fetch(f"{BASE}/{ref}")
        with open(dest, "wb") as f:
            f.write(data)
        print(f"    + chunk {os.path.basename(ref)} ({len(data)} B)")

def main():
    for slug in SLUGS:
        outdir = os.path.join(ROOT, "work", slug)
        orig = os.path.join(outdir, "index.html.orig")
        if os.path.exists(orig):
            # Pagina già mirrorata (e probabilmente già rebrandizzata): un
            # re-fetch clobbererebbe il lavoro. Skip per sicurezza.
            print(f"[{slug}] SKIP — index.html.orig già presente")
            continue
        print(f"[{slug}]")
        raw = fetch(f"{BASE}/work/{slug}").decode("utf-8", "replace")
        ensure_chunks(raw)
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, "index.html.orig"), "w", encoding="utf-8") as f:
            f.write(raw)
        with open(os.path.join(outdir, "index.html"), "w", encoding="utf-8") as f:
            f.write(rewrite(raw))
        print(f"    -> work/{slug}/index.html  ({len(raw)} B raw)")
    print("done.")

if __name__ == "__main__":
    main()
