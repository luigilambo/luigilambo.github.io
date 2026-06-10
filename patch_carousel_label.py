#!/usr/bin/env python3
"""Carousel label: drop the dot before "View project" and relabel it "Scopri di più".

Three places render that label:
  - 0nr6lqdt2xw72.js (shared canvas chunk): the VISIBLE row is
    [subtitle, 16x16 white dot, "View project", arrow]. Subtitles are now empty
    (BZN15 rebrand), so the dot is orphaned -> the dot jsx is replaced with null
    and the text relabelled. Canvas text is not hydrated -> free edit.
  - 12vmxu4i7-3qm.js (home route) / 0671of7zsd06h.js (work route): the hidden
    a11y carousel button, children ["View project: ", <span>, " ", <span>] plus
    the runtime aria-label template `View project: ${...}`.
  - mirror_root/index.html: the SSR'd a11y button text, which MUST match the
    chunk's children exactly or hydration throws a new React #418.
    (Not in the flight stream -> no T-row recompute needed.)

Idempotent; one-time backups in *.bak_label.
"""
import os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "mirror_root")
CHUNKS = os.path.join(ROOT, "_next", "static", "chunks")

DOT = '(0,ec.jsx)(wQ,{width:16,height:16,backgroundColor:"white",marginX:32,marginBottom:26,borderRadius:8})'

TARGETS = [
    (os.path.join(CHUNKS, "0nr6lqdt2xw72.js"), [
        (DOT, "null"),
        ('children:"View project"', 'children:"Scopri di più"'),
    ]),
    (os.path.join(CHUNKS, "12vmxu4i7-3qm.js"), [
        ("View project: ", "Scopri di più: "),     # a11y children + aria-label template
    ]),
    (os.path.join(CHUNKS, "0671of7zsd06h.js"), [
        ("View project: ", "Scopri di più: "),
    ]),
    (os.path.join(ROOT, "index.html"), [
        (">View project: <span></span>", ">Scopri di più: <span></span>"),  # SSR a11y button
    ]),
]

def main():
    for path, repls in TARGETS:
        data = open(path, encoding="utf-8").read()
        bak = path + ".bak_label"
        if not os.path.exists(bak):
            shutil.copyfile(path, bak)
        for old, new in repls:
            n = data.count(old)
            data = data.replace(old, new)
            print(f"  {n}x  {old[:60]!r} -> {new[:40]!r}   [{os.path.basename(path)}]")
        open(path, "w", encoding="utf-8").write(data)
    print("done.")

if __name__ == "__main__":
    main()
