#!/usr/bin/env python3
"""Home update — align the 8 carousel cards with the BZN15 service titles and
drop the subtitles; clean the ItemList JSON-LD of the 3 removed projects.

The home is NOT regenerated from index.html.orig (it carries the whole phase-2
curation); this edits mirror_root/index.html in place, idempotently:
  - card objects (NON-T flight rows): title -> cardmap title, subtitle -> ""
    (targeted by uid, so reruns are no-ops)
  - ItemList JSON-LD: removed projects dropped, positions renumbered,
    numberOfItems fixed, names relabelled by slug — applied identically to the
    static DOM <script> and to the length-prefixed T-row (T recomputed by
    edit_buffer), keeping the two copies byte-identical.
A one-time backup is kept in index.html.bak_titles.
"""
import os, re, json, shutil, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "mirror_root")

spec = importlib.util.spec_from_file_location("rw", os.path.join(HERE, "rebrand_work.py"))
rw = importlib.util.module_from_spec(spec); spec.loader.exec_module(rw)

def main():
    p = os.path.join(ROOT, "index.html")
    bak = p + ".bak_titles"
    if not os.path.exists(bak):
        shutil.copyfile(p, bak)
    html = open(p, encoding="utf-8").read()

    repls = [("fn", rw.fix_itemlist)]
    for slug in rw.KEEP:
        c = rw.CARDMAP[slug]
        repls.append(("re",
            r'("uid":"' + slug + r'","url":"/work/' + slug + r'","title":")[^"]*(","subtitle":")[^"]*(")',
            r"\g<1>" + c["title"] + r"\g<2>\g<3>"))

    bstart, bend, buf = rw.split_flight(html)
    pre = rw.apply_repls(html[:bstart], repls)
    buf = rw.edit_buffer(buf, repls)
    open(p, "w", encoding="utf-8").write(rw.emit(pre, buf, html[bend:]))

    for slug in rw.KEEP:
        m = re.search(r'"uid":"' + slug + r'","url":"[^"]*","title":"([^"]*)","subtitle":"([^"]*)"', buf)
        print(f'  {slug:22} title={m.group(1)!r} subtitle={m.group(2)!r}')
    n = re.search(r'"numberOfItems":(\d+)', buf)
    print(f'  ItemList numberOfItems={n.group(1)}')

if __name__ == "__main__":
    main()
