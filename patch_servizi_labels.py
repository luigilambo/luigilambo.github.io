#!/usr/bin/env python3
"""Patch dei chunk JS per la fase /servizi (idempotente, backup *.bak_servizi).

Quattro famiglie di modifiche, da tenere COERENTI col DOM SSR scritto da
rebrand_work.py (testi a11y identici, o l'idratazione fallisce con #418):
  1. route: i chunk costruiscono i link con template `/work/${uid}` (carosello
     home, next project a11y e canvas) -> `/servizi/${uid}`
  2. hash sezione: la mappa sezione->hash e' un'unica sorgente nel chunk
     09d2g3rtnbzgs.js (getMainPageHashRoute/getMainPageHref la derivano):
     projects:"selected-work" -> projects:"servizi"
  3. etichette detail: "Close"->"Chiudi" (canvas), "Next Project"->"Prossimo
     servizio" (canvas + a11y), "Continue"->"Continua" (bottone canvas, reset
     post-click, children a11y), aria "Continue to next project: " ->
     "Continua al prossimo servizio: "
  4. niente lunghezze da ricalcolare: i chunk non sono length-prefixed.
"""
import os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
CHUNKS = os.path.join(HERE, "mirror_root", "_next", "static", "chunks")

# (file, vecchio, nuovo) — stringhe esatte dal sorgente minificato
PATCHES = [
    # 1. route /work -> /servizi nei template literal di navigazione
    ("0671of7zsd06h.js",  "`/work/${", "`/servizi/${"),
    ("12vmxu4i7-3qm.js",  "`/work/${", "`/servizi/${"),
    ("0nr6lqdt2xw72.js",  "`/work/${", "`/servizi/${"),
    # 2. hash della sezione servizi
    ("09d2g3rtnbzgs.js",  'projects:"selected-work"', 'projects:"servizi"'),
    # 3. etichette pagina servizio
    ("0nr6lqdt2xw72.js",  '?"Close":void 0', '?"Chiudi":void 0'),
    ("0nr6lqdt2xw72.js",  'children:"Next Project"', 'children:"Prossimo servizio"'),
    ("0nr6lqdt2xw72.js",  'text:"Continue"', 'text:"Continua"'),
    ("0nr6lqdt2xw72.js",  'setProperty("text","Continue")', 'setProperty("text","Continua")'),
    ("0671of7zsd06h.js",  'children:"Next Project"', 'children:"Prossimo servizio"'),
    ("0671of7zsd06h.js",  '`Continue to next project: ${', '`Continua al prossimo servizio: ${'),
    ("0671of7zsd06h.js",  'children:"Continue"', 'children:"Continua"'),
    ("12vmxu4i7-3qm.js",  'children:"Next Project"', 'children:"Prossimo servizio"'),
    ("12vmxu4i7-3qm.js",  '`Continue to next project: ${', '`Continua al prossimo servizio: ${'),
    ("12vmxu4i7-3qm.js",  'children:"Continue"', 'children:"Continua"'),
    # 4. tipografia mobile (fase 6) — i titoli shader erano corti ("Gamily"),
    #    quelli BZN15 no: "Telecomunicazioni" a fontSize fisso 180 sborda dal
    #    viewport sotto i 1024px (v = viewport store, gia' in scope nella riga)
    ("0nr6lqdt2xw72.js",
     'fontSize:180,color:"white",textAlign:"center",lineHeight:.9,children:h.title',
     'fontSize:v.width<1024?140:180,color:"white",textAlign:"center",lineHeight:.9,children:h.title'),
    #    titolo hero: breakpoint default (<640px) leggermente piu' piccolo
    ("0nr6lqdt2xw72.js",
     'fontSize:46,lineHeight:"50px",textAlign:"center",maxWidth:"100%"',
     'fontSize:40,lineHeight:"44px",textAlign:"center",maxWidth:"100%"'),
    #    titolo pagina servizio (canvas, base 58px): "Telecomunicazioni" e' una
    #    parola sola che non puo' andare a capo e sborda sotto i 512px. Shader
    #    aveva lo STESSO problema, risolto con un'eccezione hardcoded che
    #    SILLABAVA ("Norrköpings Symfoni- orkester", ramo ormai morto): qui
    #    invece si scala il corpo quanto basta (width/10.5 ~= 37px a 390) cosi'
    #    la parola resta intera. Solo visuale canvas: l'h1 a11y resta integro.
    ("0nr6lqdt2xw72.js",
     '(0,ec.jsx)(wG,{fontSize:58,lineHeight:"58px",sm:{fontSize:64,lineHeight:"64px"},lg:{fontSize:100,lineHeight:"100px"},children:i?.title==="Norrköpings Symfoniorkester"&&u.width<512?"Norrköpings Symfoni- orkester":i?.title})',
     '(0,ec.jsx)(wG,{fontSize:i?.title==="Reti e Telecomunicazioni"&&u.width<512?Math.round(u.width/10.5):58,lineHeight:i?.title==="Reti e Telecomunicazioni"&&u.width<512?Math.round(u.width/10.5)+2+"px":"58px",sm:{fontSize:64,lineHeight:"64px"},lg:{fontSize:100,lineHeight:"100px"},children:i?.title})'),
    #    stesso caso nel titolo del blocco "Prossimo servizio" (vars E/v, base 60)
    ("0nr6lqdt2xw72.js",
     'let w=E?.title==="Norrköpings Symfoniorkester"&&v.width<512?"Norrköpings Symfoni- orkester":E?.title;f[11]!==w?(l=(0,ec.jsx)(wG,{fontSize:60,lineHeight:"60px",md:s,marginTop:32,fontWeight:"medium",lg:o,textAlign:"center",children:w})',
     'let w=E?.title;f[11]!==w?(l=(0,ec.jsx)(wG,{fontSize:E?.title==="Reti e Telecomunicazioni"&&v.width<512?Math.round(v.width/10.5):60,lineHeight:E?.title==="Reti e Telecomunicazioni"&&v.width<512?Math.round(v.width/10.5)+2+"px":"60px",md:s,marginTop:32,fontWeight:"medium",lg:o,textAlign:"center",children:w})'),
]

def main():
    for fn in sorted({f for f, _, _ in PATCHES}):
        p = os.path.join(CHUNKS, fn)
        bak = p + ".bak_servizi"
        if not os.path.exists(bak):
            shutil.copyfile(p, bak)
        src = open(p, encoding="utf-8").read()
        for f, old, new in PATCHES:
            if f != fn:
                continue
            n = src.count(old)
            src = src.replace(old, new)
            print(f"  {n}x  {old!r} -> {new!r}   [{fn}]")
        open(p, "w", encoding="utf-8").write(src)
    print("done.")

if __name__ == "__main__":
    main()
