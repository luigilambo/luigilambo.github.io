#!/usr/bin/env python3
"""Verifica integrità del flight RSC e assenza di stringhe vietate sul mirror.

Per ogni pagina:
  - ricostruisce il buffer flight (tutti i push self.__next_f) e controlla che
    OGNI riga "T<hexlen>" descriva esattamente la lunghezza UTF-8 del testo che
    segue (cioè la lunghezza cade su un confine di riga). Un errore qui = flight
    corrotto -> React #418/#423.
  - conta le stringhe "vietate" (brand/host/legali Shader, prismic, cal.com…)
    presenti nell'HTML servito.

Uso:  python3 verify_rsc.py [file ...]      (default: home + 8 pagine work)
Exit code != 0 se trova errori T-row.
"""
import os, re, sys, glob, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "mirror_root")

PUSH_RE = re.compile(r'<script>self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)</script>')
TROW_RE = re.compile(r'\n([0-9a-f]+):T([0-9a-f]+),')

# stringhe che NON devono comparire nell'HTML servito (user-facing / SEO)
FORBIDDEN = [
    "127.0.0.1", "shader.se", "shadersweden", "Shader", "prismic.io",
    "5593233140", "Norrk", "cal.com", "Cruitive", "thefwa.com",
]

def flight_buf(html):
    spans = [m.group(1) for m in PUSH_RE.finditer(html)]
    if not spans:
        return None
    return "".join(json.loads(g) for g in spans)

# un T-row è length-delimited: subito dopo i suoi `ln` byte deve iniziare la riga
# successiva (`<hexid>:`) oppure la fine del buffer. NON c'è un `\n` di mezzo.
ROW_START_RE = re.compile(r'[0-9a-f]{1,8}:')

def check_trows(buf):
    """Ritorna (n_rows, lista_errori)."""
    errs = []
    rows = list(TROW_RE.finditer(buf))
    for m in rows:
        rid, hexln, ts = m.group(1), m.group(2), m.end()
        ln = int(hexln, 16)
        raw = buf[ts:].encode("utf-8")
        if len(raw) < ln:
            errs.append(f"row {rid}: dichiara {ln}B ma restano {len(raw)}B")
            continue
        try:
            text = raw[:ln].decode("utf-8")
        except UnicodeDecodeError:
            errs.append(f"row {rid}: lunghezza {ln} spezza un carattere UTF-8")
            continue
        end = ts + len(text)
        rest = buf[end:]
        if rest and not ROW_START_RE.match(rest):
            errs.append(f"row {rid}: lunghezza {ln} non cade sull'inizio della "
                        f"riga successiva (segue {rest[:12]!r})")
    return len(rows), errs

def main(argv):
    if argv:
        files = []
        for a in argv:
            files.extend(sorted(glob.glob(a)))
    else:
        files = [os.path.join(ROOT, "index.html")] + sorted(
            glob.glob(os.path.join(ROOT, "work", "*", "index.html")))
    total_err = 0
    for f in files:
        html = open(f, encoding="utf-8").read()
        rel = os.path.relpath(f, HERE)
        buf = flight_buf(html)
        if buf is None:
            print(f"  {rel}: nessun flight push trovato"); continue
        nrows, errs = check_trows(buf)
        hits = {s: html.count(s) for s in FORBIDDEN if s in html}
        status = "OK  " if not errs and not hits else "FAIL"
        extra = f"  vietate={hits}" if hits else ""
        print(f"[{status}] {rel}  T-row {nrows - len(errs)}/{nrows}{extra}")
        for e in errs[:8]:
            print(f"      ! {e}")
        total_err += len(errs)
    print(f"--- totale errori T-row: {total_err} ---")
    return 1 if total_err else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
