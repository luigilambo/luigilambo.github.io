#!/usr/bin/env python3
"""DEPRECATED (giu 2026): superseded by rebrand_work.py, which now rebuilds the
kept pages from .orig including related-carousel cleanup, projectIds and the
coherent ica-nissen nextProject. Kept for history only — do not run.

Phase 2c — drop the 3 removed services from each kept detail page.

Every detail page's flight carries a "related projects" list with all 11 projects
plus a nextProject field. After deleting 3 services we must remove those 3 objects
from each kept page's flight (else the related carousel shows them and links 404),
and repoint ica-nissen's nextProject (was the removed norrkopings-hamn) to
ehealth-arena. The objects sit in NON-T flight rows, so removal is byte-safe.
Idempotent; runs on the already-rebranded pages.
"""
import os, re, json, sys, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "mirror_root")
spec = importlib.util.spec_from_file_location("rs", os.path.join(HERE, "remove_services.py"))
rs = importlib.util.module_from_spec(spec); spec.loader.exec_module(rs)

KEEP = ["ehealth-arena", "select-concept", "gamily", "alamance-foods",
        "son", "glasbolaget", "spp-dream-generator", "ica-nissen"]
REMOVE = ["norrkopings-hamn", "heip", "design-is-funny"]

def drop_obj(buf, slug):
    """Remove every JSON object {"uid":"<slug>",...} (array-element aware)."""
    while True:
        i = buf.find(f'{{"uid":"{slug}"')
        if i < 0:
            return buf
        st, en = rs.obj_span(buf, i)
        if buf[st - 1] == ",":                 # ,{obj}
            buf = buf[:st - 1] + buf[en:]
        elif en < len(buf) and buf[en] == ",":  # {obj},
            buf = buf[:st] + buf[en + 1:]
        else:                                   # lone {obj}
            buf = buf[:st] + buf[en:]

def process(slug):
    p = os.path.join(ROOT, "work", slug, "index.html")
    html = open(p, encoding="utf-8").read()
    bstart, bend, buf = rs.rw.split_flight(html)
    if slug == "ica-nissen":
        buf = buf.replace('"nextProject":{"uid":"norrkopings-hamn"',
                          '"nextProject":{"uid":"ehealth-arena"')
    for r in REMOVE:
        buf = drop_obj(buf, r)
    js = json.dumps(buf).replace("</", "<\\/")
    open(p, "w", encoding="utf-8").write(html[:bstart] + f"<script>self.__next_f.push([1,{js}])</script>" + html[bend:])
    left = {r: buf.count(f'{{"uid":"{r}"') for r in REMOVE}
    print(f"  {slug:20} oggetti-rimossi residui: {left}")

if __name__ == "__main__":
    sys.exit("DEPRECATED — non rilanciare: superato da rebrand_work.py "
             "(ricostruisce le pagine mantenute da .orig, related-carousel incluso).")
    for sl in KEEP:
        process(sl)
    print("done.")
