#!/usr/bin/env python3
"""Phase 2 — BZN15 rebrand of the kept /work/<slug> detail pages (all-in-one).

Rebuilds each kept page FROM index.html.orig (fully reproducible, idempotent):
  1. phase-1 length-preserving host rewrite (mirror_work_pages.rewrite) + a buffer-level
     pass that also catches URLs split across two push() calls in the raw HTML.
  2. own-page rebrand: <title>/og, <h1>, title/name JSON fields, description
     (flight via prose anchors AND the raw a11y DOM <p>, which can hold HTML
     entities like &#x27; that the prose anchors cannot match — that DOM/flight
     divergence was the source of ica-nissen's React #418).
  3. subtitles -> "" and collaborator -> "$undefined" everywhere (a11y renders
     (subtitle||collaborator)&&<p>, so both must be falsy to drop the element).
  4. "Visit site" removal: a11y <a> dropped from the DOM, every site_link ->
     {"link_type":"Any"} (the chunk renders the button only if site_link.url).
  5. related carousel: the 3 removed projects dropped from the projects array and
     from projectIds; the 8 kept titles relabelled to BZN15 page-wide.
  6. ItemList JSON-LD (DOM script + T-row): 3 removed entries dropped, positions
     renumbered, numberOfItems fixed, names relabelled by slug. DOM and flight
     copies end up byte-identical.
  7. Next Project: DOM block + flight nextProject relabelled; ica-nissen's
     nextProject is REPLACED with the real (already-rebranded) ehealth-arena
     object taken from its own related array, closing the 8-page cycle with a
     fully coherent object (uid/url/title/media all ehealth-arena).

The RSC flight stream (self.__next_f) uses byte-length-prefixed rows
("<id>:T<hexlen>,<text>"). We reconstruct the buffer from the contiguous push()
calls, edit text, RECOMPUTE every touched T-row's length, then re-emit.
"""
import os, re, json, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "mirror_root")

# reuse phase-1 host rewrite
spec = importlib.util.spec_from_file_location("mwp", os.path.join(HERE, "mirror_work_pages.py"))
mwp = importlib.util.module_from_spec(spec); spec.loader.exec_module(mwp)

CARDMAP = json.load(open(os.path.join(HERE, "cardmap.json"), encoding="utf-8"))
KEEP = ["ehealth-arena", "select-concept", "gamily", "alamance-foods",
        "son", "glasbolaget", "spp-dream-generator", "ica-nissen"]
REMOVE = ["norrkopings-hamn", "heip", "design-is-funny"]

# slug shader -> slug BZN15 (da cardmap). KEEP resta indicizzato sui vecchi slug
# (sono le chiavi di cardmap e il contenuto degli .orig); le DIRECTORY su disco
# e ogni occorrenza servita (url, uid, router state, JSON-LD) usano il nuovo.
SLUG = {s: CARDMAP[s]["slug"] for s in KEEP}

def page_dir(slug):
    return os.path.join(ROOT, "servizi", SLUG[slug])

PUSH_RE = re.compile(r'<script>self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)</script>')
TROW_RE = re.compile(r'\n([0-9a-f]+):T([0-9a-f]+),')

# ---------- flight buffer machinery ----------
def split_flight(html):
    spans = [(m.start(), m.end(), m.group(1)) for m in PUSH_RE.finditer(html)]
    buf = "".join(json.loads(g) for _, _, g in spans)
    return spans[0][0], spans[-1][1], buf

def apply_repls(text, repls):
    for r in repls:
        if r[0] == "fn":
            text = r[1](text)
        elif r[0] == "lit":
            text = text.replace(r[1], r[2])
        else:
            text = re.sub(r[1], r[2], text, flags=re.S)
    return text

def edit_buffer(buf, repls):
    out, i = [], 0
    while True:
        m = TROW_RE.search(buf, i)
        if not m:
            out.append(apply_repls(buf[i:], repls)); break
        out.append(apply_repls(buf[i:m.start()], repls))
        rid, ln, ts = m.group(1), int(m.group(2), 16), m.end()
        text = buf[ts:].encode("utf-8")[:ln].decode("utf-8")
        ntext = apply_repls(text, repls)
        nln = len(ntext.encode("utf-8"))
        out.append(f"\n{rid}:T{nln:x},{ntext}")
        i = ts + len(text)
    return "".join(out)

def emit(pre, buf, tail):
    js = json.dumps(buf).replace("</", "<\\/")   # ASCII-safe + no </script> breakout
    return pre + f"<script>self.__next_f.push([1,{js}])</script>" + tail

def obj_span(b, start):           # start = index of '{'; string-aware brace match
    depth = 0; instr = False; esc = False
    for i in range(start, len(b)):
        ch = b[i]
        if instr:
            if esc:          esc = False
            elif ch == "\\": esc = True
            elif ch == '"':  instr = False
        else:
            if ch == '"':    instr = True
            elif ch == "{":  depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0: return start, i + 1
    raise ValueError("unbalanced")

def drop_obj(buf, slug):
    """Remove every JSON object {"uid":"<slug>",...} (array-element aware)."""
    while True:
        i = buf.find(f'{{"uid":"{slug}"')
        if i < 0:
            return buf
        st, en = obj_span(buf, i)
        if buf[st - 1] == ",":                  # ,{obj}
            buf = buf[:st - 1] + buf[en:]
        elif en < len(buf) and buf[en] == ",":  # {obj},
            buf = buf[:st] + buf[en + 1:]
        else:                                   # lone {obj}
            buf = buf[:st] + buf[en:]

# ---------- ItemList JSON-LD fixer (works on DOM scripts and T-row text) ----------
ITEMLIST_RE = re.compile(r'\{"@id":"https?://[^"]*","@context":"https://schema\.org","@type":"ItemList"')

def fix_itemlist(text):
    """Drop the 3 removed projects, renumber, relabel names by slug (BZN15)."""
    out, i = [], 0
    for m in ITEMLIST_RE.finditer(text):
        st, en = obj_span(text, m.start())
        d = json.loads(text[st:en])
        items = []
        for it in d.get("itemListElement", []):
            slug = it.get("url", "").rstrip("/").rsplit("/", 1)[-1]
            if slug in REMOVE:
                continue
            if slug in CARDMAP:
                it["name"] = CARDMAP[slug]["title"]
            items.append(it)
        # ordine canonico del carosello (RANK accetta slug vecchi e nuovi)
        items.sort(key=lambda it: RANK.get(
            it.get("url", "").rstrip("/").rsplit("/", 1)[-1], 99))
        for n, it in enumerate(items):
            it["position"] = n + 1
        d["itemListElement"] = items
        d["numberOfItems"] = len(items)
        out.append(text[i:st])
        out.append(json.dumps(d, ensure_ascii=False, separators=(",", ":")))
        i = en
    out.append(text[i:])
    return "".join(out)

# ---------- per-page extraction of OLD shader strings ----------
def extract_old(orig):
    h1 = re.search(r"<h1>(.*?)</h1>", orig).group(1)
    dom_raw = re.search(r"<h1>.*?</h1><p>(.*?)</p>", orig, re.S).group(1)
    import html as H
    desc = " ".join(H.unescape(dom_raw).split())
    words = desc.split()
    return h1, dom_raw, " ".join(words[:5]), " ".join(words[-5:])

# slug -> shader h1 title, for the page-wide relabel of related/ItemList/nextProject
def old_titles():
    t = {}
    for slug in KEEP:
        orig = open(os.path.join(page_dir(slug), "index.html.orig"), encoding="utf-8").read()
        t[slug] = re.search(r"<h1>(.*?)</h1>", orig).group(1)
    return t

# tronca a confine di parola + ellissi (meta description: niente parole tagliate)
def trunc(s, n=200):
    if len(s) <= n:
        return s
    cut = s[:n]
    sp = cut.rfind(" ")
    return (cut[:sp] if sp > 40 else cut).rstrip(" ,.;:-") + "…"

# ---------- descrizioni EN dei progetti related -> IT (per uid, forma oggetto) ----------
def fix_related_descriptions(text):
    """Per ogni progetto mantenuto, riscrive la sua "description" (inglese Shader)
    con quella italiana di cardmap, ovunque compaia come oggetto {"uid":"<slug>",…}.
    Idempotente (la pagina propria e' gia' IT)."""
    for slug in KEEP:
        cdesc = CARDMAP[slug]["desc"]
        start = 0
        while True:
            i = text.find(f'{{"uid":"{slug}"', start)
            if i < 0:
                break
            st, en = obj_span(text, i)
            obj = text[st:en]
            new_obj = re.sub(r'"description":"[^"]*"',
                             lambda m: '"description":"' + cdesc + '"', obj, count=1)
            text = text[:st] + new_obj + text[en:]
            start = st + len(new_obj)
    return text

# ---------- build replacement list for one page ----------
def build_repls(slug, old_title, dom_raw, d_start, d_end, oldmap, next_slug):
    c = CARDMAP[slug]
    new_title, new_desc = c["title"], c["desc"]
    bs = r'(\\*)'                     # a run of backslashes (any nesting level)
    R = []
    # host rewrite for URLs that were split across push() boundaries in the raw HTML
    R.append(("lit", "https://www.shader.se", "http://127.0.0.1:8300"))
    # <title>/og/twitter compound (no internal quotes -> single literal at all levels)
    R.append(("lit", f"Work: {old_title} | Shader Development Studio",
                      f"Servizi: {new_title} | BZN15"))
    # a11y/DOM heading + description (raw form, may contain &#x27; entities and
    # newlines the prose anchors below can't reach — keeps DOM == flight)
    R.append(("lit", f"<h1>{old_title}</h1><p>{dom_raw}</p>",
                      f"<h1>{new_title}</h1><p>{new_desc}</p>"))
    R.append(("lit", f"<h1>{old_title}</h1>", f"<h1>{new_title}</h1>"))
    # title / name JSON fields for ALL kept projects (own header, related carousel,
    # nextProject, breadcrumb/JSON-LD), at every backslash nesting level
    for sl, old in oldmap.items():
        R.append(("re", bs + r'"(title|name)\1":\1"' + re.escape(old) + r'\1"',
                         r'\g<1>"\g<2>\g<1>":\g<1>"' + CARDMAP[sl]["title"] + r'\g<1>"'))
    # subtitles -> "" everywhere (own page, related carousel, nextProject)
    R.append(("re", bs + r'"subtitle\1":\1"[^"\\]*\1"',
                     r'\g<1>"subtitle\g<1>":\g<1>"\g<1>"'))
    # collaborator -> $undefined (renders as " with X" next to subtitles otherwise)
    R.append(("re", bs + r'"collaborator\1":\1"[^"\\]*\1"',
                     r'\g<1>"collaborator\g<1>":\g<1>"$undefined\g<1>"'))
    # site_link -> no link (chunk renders "Visit site" only when site_link.url exists)
    R.append(("re", r'"site_link":\{"link_type":"Web"[^{}]*\}',
                     '"site_link":{"link_type":"Any"}'))
    # a11y "Visit site" anchor in the DOM
    R.append(("re", r'<a target="_blank" rel="noopener noreferrer" aria-label="Visit [^"]*" href="[^"]*">Visit site</a>', ""))
    # a11y Next Project block: titolo nuovo, no subtitle <p>, href reroutato e
    # testi IT — DEVONO combaciare coi chunk patchati da patch_servizi_labels.py
    # (h2/aria/children identici, o l'idratazione fallisce con #418)
    nx = CARDMAP[next_slug]["title"]
    # the subtitle <p> may contain an SSR text-node separator: <p>Sub<!-- --> with X</p>
    R.append(("re", r'<h2>Next Project</h2><p>[^<]*</p>(?:<p>(?:[^<]|<!-- -->)*</p>)?'
                    r'<a type="button" aria-label="Continue to next project: [^"]*" href="/work/[^"]*">Continue</a>',
                    f'<h2>Prossimo servizio</h2><p>{nx}</p>'
                    f'<a type="button" aria-label="Continua al prossimo servizio: {nx}" href="/work/{next_slug}">Continua</a>'))
    # description: anchored span. Use [^<]*? (not .*?) so a match starting in the
    # truncated <meta> can't cross tag boundaries and swallow the <h1> in between.
    R.append(("re", re.escape(d_start) + r"[^<]*?" + re.escape(d_end), new_desc))
    # meta description tags (head) — no subtitle prefix anymore
    R.append(("re", r'(<meta[^>]*?(?:name|property)="(?:description|og:description|twitter:description)"[^>]*?content=")[^"]*(")',
                     r"\1" + trunc(new_desc) + r"\2"))
    # ItemList JSON-LD: drop removed, renumber, relabel (DOM script + T-row)
    R.append(("fn", fix_itemlist))

    # ===== BZN15 Fase 2: host canonico, blocco legale Org/WebSite, lang, description flight =====
    # Host del mirror -> dominio canonico apex [D1]. Sicuro nel flight (edit_buffer
    # ricalcola le T-row) e nell'head (apply_repls). Copre canonical/og:url/og:image/JSON-LD.
    R.append(("lit", "http://127.0.0.1:8300", "https://bzn15.it"))
    R.append(("re",  r'https://bzn15\.it/og(?=\\?")', "https://bzn15.it/og.jpg"))  # campo JSON-LD image
    # identita'/dati legali Shader -> BZN15. Repl sul VALORE: matcha sia la forma oggetto
    # ("…") sia la forma stringa escapata (\"…\") del flight. Ordine: piu' lungo prima.
    R.append(("lit", "Shader Sweden AB", "BZN15 s.r.l."))
    R.append(("lit", "Shader Development Studio", "BZN15"))
    R.append(("lit", r'[\"Shader\",\"Shader Sweden\"]', r'[\"BZN15\"]'))   # alternateName (flight, escaped)
    R.append(("lit", '["Shader","Shader Sweden"]', '["BZN15"]'))           # alternateName (head, unescaped)
    R.append(("lit", "hello@shader.se", "info@bzn15.it"))
    R.append(("lit", "5593233140", "IT09016880727"))
    R.append(("lit", "shadersweden", "bzn15"))
    R.append(("lit", "Based in Sweden", "Based in Italy"))
    # description Organization/meta: marketing EN (posizionamento 3D/AI errato) -> IT
    R.append(("lit",
        "Empowering Your Business with Next-Generation Interactive 3D and AI Solutions. "
        "Based in Italy and Working with Brands and Agencies Worldwide.",
        "BZN15 è una società di sistemi informatici con sede a Bari. Progettiamo, "
        "sviluppiamo e gestiamo soluzioni che integrano hardware, software, cloud e "
        "telecomunicazioni, per imprese private e pubblica amministrazione."))
    # indirizzo legale (solo forma unescaped: Org T-row + script ld+json nell'head)
    R.append(("lit", "Laxholmstorget 3", "Lungomare Starita 62"))
    R.append(("lit", '"name":"Norrköping, Sweden"', '"name":"Bari, Italy"'))
    R.append(("lit", '"addressLocality":"Norrköping"', '"addressLocality":"Bari"'))
    R.append(("lit", '"postalCode":"602 21"', '"postalCode":"70132"'))
    R.append(("lit", '"addressCountry":"SE"', '"addressCountry":"IT"'))
    R.append(("lit", '"knowsLanguage":["en","sv"]', '"knowsLanguage":["it","en"]'))
    # catch-all per eventuali "Shader" residui (nessuna parola inglese contiene "Shader")
    R.append(("lit", "Shader", "BZN15"))
    # lang dell'<html> SSR (il tag ha data-dpl-id prima di lang)
    R.append(("re", r'(<html[^>]*?)lang="en"', r'\1lang="it"'))
    # Article JSON-LD: headline "<vecchio titolo> – Website" (non coperto da title/name)
    R.append(("lit", f'"headline":"{old_title}', f'"headline":"{new_title}'))
    # meta/og/twitter description in FORMA JSON del flight (la regex HTML sopra non le copre)
    R.append(("re", r'("(?:name|property)":"(?:description|og:description|twitter:description)","content":")[^"]*(")',
                     lambda m: m.group(1) + trunc(new_desc) + m.group(2)))
    # descrizioni EN dei progetti related -> IT (per uid)
    R.append(("fn", fix_related_descriptions))
    # rimuovi isRelatedTo -> Product "Cruitive" (prodotto Shader), forma oggetto ed escapata
    R.append(("lit", ',"isRelatedTo":[{"@type":"Product","name":"Cruitive","url":"https://www.cruitive.com"}]', ""))
    R.append(("lit", r',\"isRelatedTo\":[{\"@type\":\"Product\",\"name\":\"Cruitive\",\"url\":\"https://www.cruitive.com\"}]', ""))
    # ===== slug shader -> slug BZN15. ULTIMI della lista: fix_itemlist e
    # fix_related_descriptions (sopra) indicizzano CARDMAP coi VECCHI slug.
    # Due forme, disgiunte tra loro: il path /work/<old> (url, href, canonical,
    # og:url, JSON-LD) e il bare slug come STRINGA JSON completa a ogni livello
    # di escaping ("<old>" / \"<old>\"): copre uid, projectIds e il router state
    # del flight (["uid","<old>","d"], "c":["","work","<old>"]). I chunk JS non
    # contengono slug (verificato), quindi la rinomina coerente non rompe nulla.
    for sl in KEEP:
        R.append(("lit", f"/work/{sl}", f"/work/{SLUG[sl]}"))
        R.append(("re", bs + '"' + re.escape(sl) + r'\1"',
                         r'\g<1>"' + SLUG[sl] + r'\g<1>"'))
    # ===== purga residui Shader (Article JSON-LD, media case-study, mux remoto) =====
    # headline "<titolo> – <descrittore progetto shader>" -> solo titolo
    R.append(("re", bs + r'"headline\1":\1"[^"\\]*\1"',
                     r'\g<1>"headline\g<1>":\g<1>"' + new_title + r'\g<1>"'))
    # url dell'Article -> pagina canonica (unico https esterno residuo nelle pagine;
    # gli altri campi url sono gia' bzn15 o path relativi)
    R.append(("re", bs + r'"url\1":\1"https://(?!bzn15\.it)[^"\\]*\1"',
                     r'\g<1>"url\g<1>":\g<1>"https://bzn15.it/work/' + SLUG[slug] + r'\g<1>"'))
    # contentUrl del VideoObject: stream.mux.com -> mirror locale
    R.append(("lit", "https://stream.mux.com/", "https://bzn15.it/mux/"))
    # media case-study (clip dei progetti shader) -> il video del servizio
    # stesso: ogni oggetto progetto ha il proprio mux_playback_id pochi campi
    # prima, lo si riusa via backreference (niente mappa esterna). Il gruppo
    # \3 in mezzo non puo' attraversare parentesi (resta nello stesso oggetto).
    R.append(("re", bs + r'"mux_playback_id\1":\1"([A-Za-z0-9]+)\1"([^\[\]{}]*?)"project_media\1":\[[^\]]*\]',
                     r'\g<1>"mux_playback_id\g<1>":\g<1>"\g<2>\g<1>"\g<3>'
                     r'"project_media\g<1>":[{\g<1>"mux_playback_id\g<1>":\g<1>"\g<2>\g<1>"}]'))
    # rete di sicurezza: un array rimasto multi-item (oggetto con forma diversa,
    # non riscritto sopra) conterrebbe ancora clip shader -> svuotato
    R.append(("re", bs + r'"project_media\1":\[[^\]]*,[^\]]*\]',
                     r'\g<1>"project_media\g<1>":[]'))
    # ===== route /work -> /servizi (SEMPRE ULTIMA: riscrive anche gli href
    # appena prodotti dalle regex sopra). Tre forme: path (/work/ e /work a fine
    # url tipo breadcrumb "@id"), router state RSC (["","work","<slug>"] e
    # ["work",{"children":...]) e nome breadcrumb "Work".
    R.append(("re", r'/work(?=[/\\"])', "/servizi"))
    R.append(("re", bs + r'"work\1"', r'\g<1>"servizi\g<1>"'))
    R.append(("re", bs + r'"name\1":\1"Work\1"', r'\g<1>"name\g<1>":\g<1>"Servizi\g<1>"'))
    return R

# ---------- structural buffer ops (run after the textual repls) ----------
def fix_structure(buf, slug):
    # pagine con catena next reindirizzata (NEXT_OVERRIDE): il nextProject del
    # flight punta ancora al target shader originale -> si sostituisce l'INTERO
    # oggetto col target REALE (gia' rebrandato) copiato dal related array della
    # pagina, cosi' uid/url/title/media restano coerenti. Gli uid sono gia'
    # BZN15: fix_structure gira DOPO edit_buffer, quindi dopo la rinomina slug.
    if slug in NEXT_OVERRIDE:
        target = SLUG[NEXT_OVERRIDE[slug]]
        i = buf.find('"nextProject":{')
        st, en = obj_span(buf, i + len('"nextProject":'))
        j = buf.find('{"uid":"' + target + '"')
        assert 0 <= j < st, f"related {target} object not found before nextProject"
        rst, ren = obj_span(buf, j)
        buf = buf[:st] + buf[rst:ren] + buf[en:]
    # drop the 3 removed projects from the related carousel
    for r in REMOVE:
        buf = drop_obj(buf, r)
    # and from projectIds (always listed last, contiguously)
    buf = buf.replace(',"norrkopings-hamn","heip","design-is-funny"', "")
    # ordine canonico del carosello (sviluppo-software-e-saas per primo)
    return reorder_projects(buf)

# ordine del carosello (fase 7, scelto dall'utente): Sviluppo, Cybersecurity,
# Governance, Infrastrutture, Reti, Gestione, Impiantistica, Formazione.
ORDER = ["alamance-foods", "ehealth-arena", "select-concept", "gamily",
         "son", "glasbolaget", "spp-dream-generator", "ica-nissen"]

# La catena "Prossimo servizio" segue l'ordine del carosello (ciclica). Dove
# diverge dal nextProject originale shader (catena orig: ehealth->select->
# gamily->alamance->son->glasbolaget->spp->ica) serve l'override, che in
# fix_structure sostituisce l'INTERO oggetto nextProject del flight.
NEXT_OVERRIDE = {
    "alamance-foods": "ehealth-arena",   # svil -> cyber (orig: -> son)
    "gamily": "son",                     # infra -> reti (orig: -> alamance)
    "ica-nissen": "alamance-foods",      # form -> svil, chiude il ciclo
}
# rank per vecchio E nuovo slug (serve in stadi diversi della pipeline)
RANK = {s: i for i, s in enumerate(ORDER)}
RANK.update({SLUG[s]: i for i, s in enumerate(ORDER)})

def reorder_projects(buf):
    """Riordina l'array "projects" (per uid) e "projectIds" secondo ORDER.
    Gira DOPO la rinomina slug, quindi cerca gli uid NUOVI. No-op se l'array
    non contiene esattamente gli 8 kept (pagine future-proof)."""
    order_new = [SLUG[s] for s in ORDER]
    i = buf.find('"projects":[')
    if i >= 0:
        st = i + len('"projects":')
        objs, pos, end = {}, st + 1, None
        while pos < len(buf) and buf[pos] == "{":
            ost, oen = obj_span(buf, pos)
            o = buf[ost:oen]
            m = re.search(r'"uid":"([a-z0-9-]+)"', o)
            if m:
                objs[m.group(1)] = o
            pos = oen + 1 if oen < len(buf) and buf[oen] == "," else oen
            if pos < len(buf) and buf[pos] == "]":
                end = pos + 1
                break
        if end and set(objs) == set(order_new):
            buf = buf[:st] + "[" + ",".join(objs[u] for u in order_new) + "]" + buf[end:]
    m = re.search(r'"projectIds":\[("[a-z0-9-]+"(?:,"[a-z0-9-]+")*)\]', buf)
    if m:
        ids = re.findall(r'"([a-z0-9-]+)"', m.group(1))
        if set(ids) == set(order_new):
            buf = (buf[:m.start()] + '"projectIds":['
                   + ",".join(f'"{u}"' for u in order_new) + "]" + buf[m.end():])
    return buf

def main():
    oldmap = old_titles()
    for slug in KEEP:
        p = page_dir(slug)
        orig = open(os.path.join(p, "index.html.orig"), encoding="utf-8").read()
        old_title, dom_raw, d_start, d_end = extract_old(orig)
        next_slug = re.search(r'nextProject\\":\{\\"uid\\":\\"([a-z-]+)', orig).group(1)
        next_slug = NEXT_OVERRIDE.get(slug, next_slug)   # keyed by PAGE, not by target
        repls = build_repls(slug, old_title, dom_raw, d_start, d_end, oldmap, next_slug)
        html = mwp.rewrite(orig)              # phase-1 host rewrite (length-preserving)
        bstart, bend, buf = split_flight(html)
        pre = apply_repls(html[:bstart], repls)
        buf = fix_structure(edit_buffer(buf, repls), slug)
        open(os.path.join(p, "index.html"), "w", encoding="utf-8").write(
            emit(pre, buf, html[bend:]))
        print(f"[{slug:20}] {old_title!r} -> {CARDMAP[slug]['title']!r}  next={next_slug}")
    print("done.")

if __name__ == "__main__":
    main()
