#!/usr/bin/env python3
"""PARTLY DEPRECATED (giu 2026): remove_home_cards/delete_dirs were one-shot and
already applied; reroute_ica is superseded by rebrand_work.py (coherent
nextProject rebuilt from .orig). Home title/subtitle/ItemList edits now live in
update_home.py. Do not re-run.

Phase 2b — remove the 3 non-kept services.

- HOME: drop the 3 project cards (norrkopings-hamn, heip, design-is-funny) from the
  carousel array in the flight buffer. The card objects live in a NON-T (regular)
  flight row, so deleting them is byte-length-safe (T-rows untouched).
- Reroute ica-nissen's "Next Project" (was -> removed norrkopings-hamn) to
  ehealth-arena, closing the 8-service cycle. Done via the flight-aware editor
  (recomputes T-rows).
- Delete the 3 detail page directories.

NOTE: the breadcrumb/ItemList JSON-LD on the home still lists the 3 removed
projects (SEO-only, invisible, sits in length-prefixed T-rows) — left untouched.
"""
import os, re, json, shutil, sys, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "mirror_root")

spec = importlib.util.spec_from_file_location("rw", os.path.join(HERE, "rebrand_work.py"))
rw = importlib.util.module_from_spec(spec); spec.loader.exec_module(rw)

REMOVE = ["norrkopings-hamn", "heip", "design-is-funny"]

def obj_span(b, start):           # start = index of '{'; string-aware brace match
    depth = 0; instr = False; esc = False
    for i in range(start, len(b)):
        ch = b[i]
        if instr:
            if esc:        esc = False
            elif ch == "\\": esc = True
            elif ch == '"':  instr = False
        else:
            if ch == '"':   instr = True
            elif ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0: return start, i + 1
    raise ValueError("unbalanced")

def remove_home_cards():
    p = os.path.join(ROOT, "index.html")
    html = open(p, encoding="utf-8").read()
    bstart, bend, buf = rw.split_flight(html)
    for slug in REMOVE:
        i = buf.find(f'{{"uid":"{slug}","url":"/work/{slug}"')
        if i < 0:
            print(f"  card {slug}: NON trovata"); continue
        st, en = obj_span(buf, i)
        # also swallow the preceding comma (cards are never first in the array)
        cut = st - 1 if buf[st - 1] == "," else st
        buf = buf[:cut] + buf[en:]
        print(f"  card {slug}: rimossa ({en - st} char)")
    js = json.dumps(buf).replace("</", "<\\/")
    open(p, "w", encoding="utf-8").write(html[:bstart] + f"<script>self.__next_f.push([1,{js}])</script>" + html[bend:])

def reroute_ica():
    p = os.path.join(ROOT, "work", "ica-nissen", "index.html")
    html = open(p, encoding="utf-8").read()
    c = rw.CARDMAP["ehealth-arena"]           # new "next" target
    repls = [
        ("lit", "/work/norrkopings-hamn", "/work/ehealth-arena"),
        ("lit", "Continue to next project: Norrköpings Hamn",
                f"Continue to next project: {c['title']}"),
        ("lit", "Norrköpings Hamn", c["title"]),     # next-project label
        ("lit", "3D Flow Visualization", c["sub"]),  # next-project category
    ]
    open(p, "w", encoding="utf-8").write(rw.rebrand_html(html, repls))
    print(f"  ica-nissen Next Project -> ehealth-arena ({c['title']})")

def delete_dirs():
    for slug in REMOVE:
        d = os.path.join(ROOT, "work", slug)
        if os.path.isdir(d):
            shutil.rmtree(d); print(f"  cartella work/{slug} eliminata")

if __name__ == "__main__":
    sys.exit("DEPRECATED — non rilanciare: rotto (usa rw.rebrand_html inesistente). "
             "Le modifiche home vivono in update_home.py; le work in rebrand_work.py.")
    print("HOME: rimozione card"); remove_home_cards()
    print("REROUTE:"); reroute_ica()
    print("DELETE detail dirs:"); delete_dirs()
    print("done.")
