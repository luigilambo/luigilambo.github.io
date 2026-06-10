#!/usr/bin/env python3
"""Fase 1.8 [D5] — neutralizza l'easter egg FWA nel chunk 0nr6lqdt2xw72.js.

Svuota i CONTENUTI (markdown del rant "award/Sweden/lagom", headline, riga di
chiusura) e annulla la funzione LF() che apre il case study Shader su thefwa.com,
SENZA eliminare funzioni: il modulo resta sintatticamente intatto. I 2 easter egg
da tenere (shredder, cravatta d'oro) non sono qui e restano intatti.

Idempotente. Backup .bak_fwa. Il chunk e' grande (2.3MB) e va girato fuori dal
sandbox del tool Bash (lettura/scrittura piena bloccata con EPERM).
"""
import os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
CHUNK = os.path.join(HERE, "mirror_root", "_next", "static", "chunks", "0nr6lqdt2xw72.js")

def string_end(s, q):
    """q = indice della virgoletta di apertura; ritorna l'indice DOPO quella di
    chiusura non escapata."""
    i = q + 1
    while i < len(s):
        c = s[i]
        if c == "\\":
            i += 2; continue
        if c == '"':
            return i + 1
        i += 1
    raise ValueError("stringa non terminata")

LITERALS = [
    ('children:"BZN15 wins FWA Site of the Day"', 'children:""'),
    ('children:"Una pagina in meno da leggere. Prego, non ringraziate."', 'children:""'),
    ('window.open("https://thefwa.com/cases/shader-development-studio","_blank")', 'null'),
]

def main():
    bak = CHUNK + ".bak_fwa"
    if not os.path.exists(bak):
        shutil.copyfile(CHUNK, bak)
    s = before = open(CHUNK, encoding="utf-8").read()

    # 1) svuota la stringa markdown assegnata a Lv (rant FWA, scansione escape-aware)
    a = s.find('let Lv="')
    if a >= 0:
        q = a + len("let Lv=")
        e = string_end(s, q)
        s = s[:q] + '""' + s[e:]

    # 2) headline / riga chiusura / link thefwa.com
    for old, new in LITERALS:
        s = s.replace(old, new)

    open(CHUNK, "w", encoding="utf-8").write(s)
    print("0nr6: FWA neutralizzata" if s != before else "0nr6: gia' neutralizzata (no-op)")
    for tok in ("thefwa.com", "lagom", "FWA Site of the Day", "Will Never Win an Award"):
        print(f"  residuo '{tok}': {s.count(tok)}")

if __name__ == "__main__":
    main()
