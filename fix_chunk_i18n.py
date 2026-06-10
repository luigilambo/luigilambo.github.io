#!/usr/bin/env python3
"""Fasi 1+3 — allinea i chunk user-facing al brand/lingua BZN15 e fa combaciare i
gemelli (0671 work ↔ 12vmxu4i7 home: stessi module id -> in SPA vince l'ultimo
registrato, quindi le stringhe devono combaciare parola per parola).

Repl per-chunk + backup .bak_i18n. Idempotente (le stringhe vecchie spariscono).
Tutte le "Shader" toccate sono stringhe (aria-label/children), mai identificatori;
le "Shader" di Three.js (ShaderMaterial, vertexShader…) NON sono qui interessate.
"""
import os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
CHUNKS = os.path.join(HERE, "mirror_root", "_next", "static", "chunks")

# cal.com -> #contatti [D2]: aria-label CTA + config URL "bookACall"
CAL_ARIA = [
    ("Book a call with Shader on Cal.com, opens in new tab", "Prenota una call"),
    ("Book a call with BZN15 on Cal.com, opens in new tab", "Prenota una call"),
    ("Book a call on Cal.com, opens in new tab", "Prenota una call"),
    ('bookACall:"https://cal.com/bzn15"', 'bookACall:"#contatti"'),
]

PER_CHUNK = {
    # chunk di route work: brand + traduzioni del gemello home
    "0671of7zsd06h.js": [
        ("Shader", "BZN15"),
        ("Book a Call Today", "Prenota una call"),
        ("Reach out today to our CEO for new business enquiries at ",
         "Volete fare business con noi? Scrivete direttamente al nostro CEO: "),
        ("Accessibility Statement navigation", "Dichiarazione di accessibilità navigation"),
        ("Accessibility Statement", "Dichiarazione di accessibilità"),
    ] + CAL_ARIA,
    # chunk gemello home: nome unico sezione [D6] + cal aria
    "12vmxu4i7-3qm.js": [
        ("Lavori Selezionati", "Servizi"),
        ("Cosa facciamo", "Servizi"),
    ] + CAL_ARIA,
    # chunk condiviso: cal aria
    "09d2g3rtnbzgs.js": list(CAL_ARIA),
}

def main():
    for name, repls in PER_CHUNK.items():
        path = os.path.join(CHUNKS, name)
        if not os.path.exists(path):
            print(f"  {name}: ASSENTE, skip"); continue
        bak = path + ".bak_i18n"
        if not os.path.exists(bak):
            shutil.copyfile(path, bak)
        s = before = open(path, encoding="utf-8").read()
        for old, new in repls:
            s = s.replace(old, new)
        open(path, "w", encoding="utf-8").write(s)
        resid = s.count("Cal.com") + s.count("Lavori Selezionati") + s.count("Cosa facciamo")
        tag = "modificato" if s != before else "no-op"
        print(f"  {name}: {tag}  (residui cal/label user-facing: {resid})")

if __name__ == "__main__":
    main()
