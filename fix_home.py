#!/usr/bin/env python3
"""Fase 1 — home (mirror_root/index.html): correzioni SSR + flight RSC.

Edita in place, idempotente, backup .bak_fase1. Le T-row del flight sono
ricalcolate da rw.edit_buffer (mai a mano). Copre:
  - host canonico apex [D1]: www.bzn15.it -> bzn15.it (NON tocca i social www.*)
  - provider.@id Shader -> bzn15 (unica shader.se rimasta, solo nel flight)
  - knowsLanguage ["en","sv"] -> ["it","en"]
  - og:image Prismic (4) -> /og.jpg propria; logo dark-colored.png -> og.jpg
  - ItemList @id /work (404) -> home
  - isRelatedTo Product "Cruitive" rimosso (oggetto + forma escapata)
  - site_link dei 7 clienti svuotati [D4] -> {"link_type":"Any"}
  - CTA cal.com [D2]: href -> #contatti, aria-label -> "Prenota una call",
    interceptor inline cal.com rimosso dalla coda
  - refuso un\\'idea -> un&#x27;idea
  - sezione lavori: h2 "Alcuni Lavori" -> "Servizi" [D6] (lato chunk: fix_chunk_i18n)
  - lang dell'<html> SSR -> it
"""
import os, re, json, shutil, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "mirror_root")
spec = importlib.util.spec_from_file_location("rw", os.path.join(HERE, "rebrand_work.py"))
rw = importlib.util.module_from_spec(spec); spec.loader.exec_module(rw)

CAL_ARIA = [
    ("Book a call with BZN15 on Cal.com, opens in new tab", "Prenota una call"),
    ("Book a call on Cal.com, opens in new tab", "Prenota una call"),
]

def build_repls():
    R = []
    R.append(("lit", "www.bzn15.it", "bzn15.it"))            # [D1] apex (no social www.*)
    R.append(("lit", "www.shader.se", "bzn15.it"))           # provider.@id
    # meta/og/twitter + Org description: marketing EN (3D/AI) -> IT, tutte le 8 occorrenze
    R.append(("lit",
        "Empowering Your Business with Next-Generation Interactive 3D and AI Solutions. "
        "Based in Italy and Working with Brands and Agencies Worldwide.",
        "BZN15 è una società di sistemi informatici con sede a Bari. Progettiamo, "
        "sviluppiamo e gestiamo soluzioni che integrano hardware, software, cloud e "
        "telecomunicazioni, per imprese private e pubblica amministrazione."))
    R.append(("lit", '"knowsLanguage":["en","sv"]', '"knowsLanguage":["it","en"]'))
    R.append(("re",  r'https://images\.prismic\.io/shader/[^"\\]*', "https://bzn15.it/og.jpg"))
    R.append(("re",  r'https://bzn15\.it/og(?=\\?")', "https://bzn15.it/og.jpg"))  # campo JSON-LD image
    R.append(("lit", "bzn15.it/dark-colored.png", "bzn15.it/og.jpg"))    # logo JSON-LD
    R.append(("lit", '"@id":"https://bzn15.it/work","@context":"https://schema.org","@type":"ItemList"',
                     '"@id":"https://bzn15.it","@context":"https://schema.org","@type":"ItemList"'))
    R.append(("lit", ',"isRelatedTo":[{"@type":"Product","name":"Cruitive","url":"https://www.cruitive.com"}]', ""))
    R.append(("lit", r',\"isRelatedTo\":[{\"@type\":\"Product\",\"name\":\"Cruitive\",\"url\":\"https://www.cruitive.com\"}]', ""))
    # JSON-LD @type:Service: il testo era ancora il posizionamento Shader in inglese
    # (3D/AI per brand worldwide). Riscritto su BZN15/IT. name/description/serviceType
    # compaiono identici in SSR e flight -> repl uniche le allineano entrambe (T-row
    # del flight ricalcolate da edit_buffer). areaServed:"Worldwide" lasciato invariato:
    # la sua forma Country differisce tra le due copie, sostituirla le desincronizzerebbe.
    R.append(("lit", "Creative Development Services",
                     "Sistemi informatici e telecomunicazioni"))
    R.append(("lit", "Interactive 3D experiences, AI solutions, and full-stack development for brands worldwide.",
                     "Progettazione, sviluppo e gestione di soluzioni che integrano hardware, "
                     "software, cloud e telecomunicazioni, per imprese private e pubblica amministrazione."))
    R.append(("lit", "Interactive 3D & AI Development",
                     "Sistemi informatici, cloud e telecomunicazioni"))
    # Organization.knowsAbout: 8 competenze Shader (3D/AI/agency) -> 8 servizi canonici
    # BZN15 (gli stessi titoli delle pagine work). Ogni elemento compare 2x (SSR+flight):
    # repl per-elemento le allinea entrambe senza desync (l'array intero ha formattazione
    # diversa tra le copie, quindi NON si sostituisce in blocco).
    for old, new in [
        ("Interactive 3D design and development",      "Sviluppo software e SaaS"),
        ("AI-powered content creation",                "Cybersecurity"),
        ("3D configurator development",                "Infrastrutture e Cloud"),
        ("3D modeling and animation",                  "Gestione di sistemi e applicazioni"),
        ("Creative concept development and strategy",  "Formazione e consulenza"),
        ("Full-stack development",                     "Governance, rischio e conformità"),
        ("UI and motion design",                       "Reti e telecomunicazioni"),
        ("Agency services",                            "Impiantistica tecnologica"),
    ]:
        R.append(("lit", old, new))
    # WebSite.description: ancora il claim Shader inglese -> BZN15/IT
    R.append(("lit",
        "Creative development studio specialized in interactive 3D and AI solutions.",
        "Società di sistemi informatici con sede a Bari: hardware, software, cloud e "
        "telecomunicazioni per imprese e pubblica amministrazione."))
    R.append(("re",  r'"site_link":\{"link_type":"Web"[^{}]*\}', '"site_link":{"link_type":"Any"}'))
    R.append(("lit", 'href="https://cal.com/bzn15"', 'href="#contatti"'))
    for old, new in CAL_ARIA:
        R.append(("lit", old, new))
    # CTA "Prenota una call" della navbar: il client la rende senza target/rel e con
    # aria "Vai alla sezione Contatti" -> allineo l'SSR (mismatch HTML #418)
    R.append(("lit",
        '<a href="#contatti" target="_blank" rel="noopener noreferrer" aria-label="Prenota una call">Prenota una call</a>',
        '<a href="#contatti" aria-label="Vai alla sezione Contatti">Prenota una call</a>'))
    # NB: refuso, nome sezione "Servizi", paragrafo e About 9-paragrafi sono gestiti
    # dal riallineamento integrale delle sezioni a11y in main() (home_sections.json).
    R.append(("re",  r'(<html[^>]*?)lang="en"', r'\1lang="it"'))
    # [F1.5] lang anche nel flight: il root layout RSC porta {"lang":"en"} sull'elemento
    # <html>; se non patchato qui, il client idrata lang="en" sul DOM SSR lang="it" ->
    # mismatch sull'elemento <html> = React #418 (args[]=HTML). en->it è byte-identico.
    R.append(("lit", '"lang":"en"', '"lang":"it"'))
    return R

def main():
    p = os.path.join(ROOT, "index.html")
    bak = p + ".bak_fase1"
    if not os.path.exists(bak):
        shutil.copyfile(p, bak)
    html = open(p, encoding="utf-8").read()
    repls = build_repls()
    bstart, bend, buf = rw.split_flight(html)
    pre = rw.apply_repls(html[:bstart], repls)
    # riallinea le sezioni a11y SSR all'ESATTO render del client (chunk): elimina i
    # mismatch di hydration #418/#423 (h1 newline, nome sezione, About 9 paragrafi…).
    sections = json.load(open(os.path.join(HERE, "home_sections.json"), encoding="utf-8"))
    for lbl, new_html in sections.items():
        pat = r'<section aria-label="' + re.escape(lbl) + r'"[^>]*>.*?</section>'
        pre, n = re.subn(pat, lambda m, h=new_html: h, pre, count=1, flags=re.S)
        if n == 0:
            print(f"  ! sezione a11y '{lbl}' non trovata nell'SSR")
    buf = rw.edit_buffer(buf, repls)
    tail = html[bend:]
    # rimuovi l'interceptor inline cal.com (unico IIFE nella coda)
    tail = re.sub(r'<script>\(function\(\)\{.*?\}\)\(\);</script>', '', tail, flags=re.S)
    open(p, "w", encoding="utf-8").write(rw.emit(pre, buf, tail))
    print("home aggiornata (Fase 1)")

if __name__ == "__main__":
    main()
