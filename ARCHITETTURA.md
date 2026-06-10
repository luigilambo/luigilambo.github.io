# Documento architetturale — Sito 3D BZN15 (mirror di shader.se)

> **Domanda a cui risponde questo documento:** com'è possibile che un sito pieno
> di contenuti 3D, shader e video sia comunque leggero da caricare e fluido da
> usare?
>
> **Risposta breve:** non lo è per caso. È il risultato di tre principi applicati
> con disciplina — *comprimi tutto ciò che deve arrivare subito*, *trasforma in
> streaming ciò che è troppo grande*, *disegna il 3D con il minor numero di draw
> call possibile* — il tutto orchestrato da Next.js + React Three Fiber.

---

## 1. Contesto

Questo progetto è un **mirror locale, completamente autonomo, del sito
`https://www.shader.se/`**, in corso di rebranding verso **BZN15**
(`https://www.bzn15.it`). Non è una ricostruzione: è il sito *reale* — l'HTML
originale generato da Next.js, i bundle JS/CSS effettivi (il vero codice
React-Three-Fiber + WebGL), i modelli 3D compressi con Draco, le texture, i
font, lo shader della schermata di boot CRT, e tutti i video Mux scaricati in
locale.

L'obiettivo del mirror è far girare l'intera esperienza **senza alcuna richiesta
di terze parti**: una sessione completa genera ~93 richieste, tutte verso
`127.0.0.1`.

| | |
|---|---|
| **Origine** | shader.se (Next.js + React Three Fiber) |
| **Brand di destinazione** | BZN15 |
| **Server locale** | `serve.py` (porta 8300, threaded) |
| **Root servita** | `mirror_root/` |
| **Indipendenza** | Mux, Draco e analytics ri-puntati su path locali |

---

## 2. Stack tecnologico

```
┌─────────────────────────────────────────────────────────────┐
│  Next.js (App Router, Turbopack)        → HTML + code-split   │
│  React                                  → UI / DOM            │
│  React Three Fiber (R3F)                → ponte React ↔ Three │
│  Three.js (WebGLRenderer)               → motore 3D           │
│  ├─ DRACOLoader (+ WASM)                → decompressione mesh │
│  ├─ KTX2 / meshopt                      → texture GPU-ready   │
│  └─ InstancedMesh                       → batching draw call  │
│  HLS.js + Mux                           → video in streaming  │
│  Lenis                                  → smooth scroll       │
│  Shader GLSL custom                     → boot screen CRT     │
└─────────────────────────────────────────────────────────────┘
```

Tutte le librerie sono confermate per presenza nel bundle principale
`_next/static/chunks/0nr6lqdt2xw72.js` (Three.js, DRACOLoader, KTX2,
MeshoptDecoder, react-three/fiber, WebGLRenderer, InstancedMesh, HLS, Lenis).

---

## 3. Architettura di rendering

### 3.1 Un solo canvas WebGL per l'intera pagina

Il sito **non** crea un canvas 3D per sezione. Esiste un singolo
`WebGLRenderer` / una singola scena R3F che copre l'intera narrazione di
scroll (hero → desk → shredder → golden-tie → bank → footer). Le sezioni sono
oggetti diversi *nella stessa scena*, montati e smontati in base alla posizione
di scroll. Questo evita il costo (memoria GPU, context switch) di più contesti
WebGL coesistenti.

### 3.2 Scroll guidato → camera/timeline

Lo scroll è gestito da **Lenis** (smooth scroll) e tradotto in una timeline che
pilota camera e stato delle scene. Il DOM scorre, ma ciò che l'utente percepisce
come "animazione 3D" è la scena WebGL che reagisce al progresso di scroll. È un
unico loop di render, non N animazioni indipendenti.

### 3.3 Instancing

`InstancedMesh` compare 7 volte nel bundle. L'instancing permette di disegnare
molti oggetti identici con **una sola draw call** invece di una per oggetto. È la
leva principale della *fluidità* (frame rate stabile), distinta dalla leggerezza
(peso di rete).

> **Distinzione chiave:** *leggerezza* = pochi byte scaricati (sezioni 4–5).
> *reattività* = pochi millisecondi per frame (sezione 3 + 6).

---

## 4. Pipeline degli asset

L'intera strategia di performance si riassume così: ogni tipo di asset usa il
formato più aggressivo possibile per il suo scopo.

### 4.1 Modelli 3D — Draco

`models/` contiene 7 modelli `.glb`, per **1,3 MB in totale**:

| modello | peso |
|---|---|
| `bank.glb` | 427 KB |
| `deskbox.glb` | 256 KB |
| `trophy2.glb` | 236 KB |
| `phones.glb` | 214 KB |
| `computer.glb` | 149 KB |
| `shredder.glb` | 25 KB |
| `tie.glb` | 23 KB |

La geometria è compressa con **Draco** (quantizzazione + compressione). Il
decoder vive in `draco/`:

- `draco_decoder.wasm` — 283 KB (decoder WebAssembly)
- `draco_decoder.js` / `draco_wasm_wrapper.js` — bootstrap

**Perché funziona:** il decoder è WebAssembly, scaricato *una volta sola* e
configurato via `setDecoderPath` / `setDecoderConfig` (visibili nel bundle); la
decompressione gira fuori dal main thread. Si paga un costo fisso (283 KB) per
risparmiare megabyte su *ogni* mesh. Nel mirror il decoder, prima servito da
`www.gstatic.com`, è stato ri-puntato su `/draco/`.

### 4.2 Texture — WebP + KTX2/meshopt

`textures/` contiene 15 WebP contro pochi PNG residui, per **~2,0 MB** totali.
WebP pesa il 25–35% in meno di PNG/JPG a parità qualità. Il bundle supporta
inoltre **KTX2/Basis** e **meshopt**: texture compresse leggibili direttamente
dalla GPU, che riducono non solo la banda ma anche la **VRAM** occupata.

### 4.3 Video — Mux in HLS (il punto cruciale)

`mux/` pesa **74 MB** — più di tutto il resto messo insieme. Ma **non viene mai
scaricata interamente.** I video sono serviti in **HLS** (`.m3u8` manifest +
segmenti `.ts`) tramite **Mux**, e il player **HLS.js** scarica:

1. il manifest,
2. solo pochi segmenti alla volta,
3. alla risoluzione adatta alla connessione (adaptive bitrate).

Quei 74 MB sono il *catalogo completo a tutte le qualità*: l'utente ne riceve una
frazione progressiva. È il motivo per cui un sito "pieno di video" parte
istantaneo. Nel mirror i 53 video, prima da `stream.mux.com`, sono stati
scaricati con `ffmpeg` in HLS multi-segmento locale e i bundle ri-puntati.

Esiste anche un **fallback prebaked**: `videos/prebaked/*_avif/` contiene clip
come sprite-sheet AVIF (es. `handshake_sheet_000.avif` + `manifest.json`, ~860 KB
totali) per scenari dove l'HLS non è disponibile o per micro-animazioni.

### 4.4 Font — due percorsi

| uso | formato | dove |
|---|---|---|
| testo HTML/DOM | `.woff2` (1 file, `preload`ato) | `_next/static/media/` |
| testo dentro la scena 3D | atlas `.json` (metriche) + `.png` (glifi) | `fonts/stix_*` |

Il testo renderizzato **dentro WebGL** non usa font vettoriali: usa atlas STIX
(coppie JSON+PNG, ~80–125 KB ciascuna) — i glifi sono pre-renderizzati in una
texture e disegnati come quad. Questo evita di triangolare font a runtime.

### 4.5 Boot screen — shader CRT

La schermata d'avvio è un vero **shader WebGL GLSL** (effetto CRT), non un
video né una GIF: pochi byte di codice che generano l'effetto sulla GPU.
`textures/boot_screen.png` (334 KB) è l'asset di supporto.

---

## 5. Strategia di caricamento (Next.js)

### 5.1 Code splitting

Il JS in `_next/static/chunks/` è spezzato in **decine di chunk piccoli**,
caricati con `async`. Esiste un chunk grosso (`0nr6lqdt2xw72.js`, 2,3 MB — è
Three.js + R3F + l'app), ma il resto è frammentato e tirato on-demand. Peso JS
totale ~3,5 MB non compresso (molto meno in gzip/brotli sul vero server).

### 5.2 Preload mirato

Nell'`<head>` di `index.html` i `preload` sono **selettivi**, non a tappeto:

- **1×** `preload as="font"` → il woff2 critico (anti-FOUT)
- **CSS critico** caricato con `data-precedence`
- gli script 3D pesanti restano `async` e vengono idratati *dopo* il first paint

Questo significa: il browser dà priorità a ciò che rende la pagina *visivamente
pronta*, e monta le scene 3D in un secondo momento.

### 5.3 Montaggio progressivo delle scene

Le scene 3D vengono montate in funzione dello scroll: gli asset (GLB, texture,
segmenti video) di una sezione vengono richiesti quando la sezione si avvicina
al viewport, non tutti all'avvio. Lo scroll diventa quindi anche la strategia di
*lazy-loading*.

---

## 6. Perché risulta leggero E reattivo — sintesi

**Leggero (rete)** — quello che *sembra* enorme arriva al browser così:

```
modelli 3D (Draco)    1,3 MB   ← on-demand per sezione
texture (WebP/KTX2)   2,0 MB   ← compresse, GPU-ready
JS app (chunked)     ~3,5 MB   ← code-split + preload mirato (gzip ≪)
font woff2 + atlas   ~0,5 MB   ← 1 woff2 preload + atlas SDF
video (HLS/Mux)        74 MB   ← MA scaricato a pezzi, MAI tutto
─────────────────────────────
sul primo schermo l'utente scarica una piccola frazione del totale
```

**Reattivo (runtime):**

- un **solo** contesto WebGL riusato per tutta la pagina;
- **instancing** per minimizzare le draw call;
- decompressione Draco in **WASM** fuori dal main thread;
- texture **GPU-ready** (KTX2) che non vanno transcodificate a runtime;
- **smooth scroll** (Lenis) che disaccoppia l'input dal rendering.

La regola generale, applicabile a qualsiasi sito 3D:

> **Comprimi aggressivamente ciò che deve arrivare subito (Draco, WebP, KTX2),
> trasforma in streaming ciò che è troppo grande (video HLS), e disegna con il
> minor numero di draw call possibile (instancing, un solo canvas).**

---

## 7. Struttura delle directory

```
mirror/
├── serve.py                  # server locale (porta 8300, threaded)
├── ARCHITETTURA.md           # questo documento
├── README.md                 # istruzioni del mirror
└── mirror_root/              # root servita
    ├── index.html            # HTML Next.js (head con preload mirati)
    ├── _next/
    │   └── static/
    │       ├── chunks/        # bundle JS/CSS (code-split)
    │       │   └── 0nr6lqdt2xw72.js   # bundle principale (Three+R3F+app)
    │       └── media/         # woff2 + asset statici
    ├── models/*.glb          # 7 modelli 3D Draco (1,3 MB)
    ├── draco/                # decoder Draco WASM (era gstatic)
    ├── textures/             # WebP/PNG/SVG + boot_screen.png
    ├── fonts/stix_*          # atlas font 3D (JSON metriche + PNG glifi)
    ├── mux/                  # 53 video HLS locali (.m3u8 + .ts, era stream.mux.com)
    ├── videos/prebaked/      # fallback clip come sprite-sheet AVIF
    ├── _a/script.js          # analytics no-op (era analytics.shader.build)
    └── api/mux-image/        # poster del carosello progetti (+ fallback)
```

---

## 8. Il server locale (`serve.py`)

Un semplice handler HTTP threaded che rende il mirror autonomo:

- ignora la query `?dpl=…` che Next.js appende agli URL dei chunk;
- imposta i MIME corretti per HLS (`application/vnd.apple.mpegurl`), `.ts` e
  `.wasm` (`application/wasm`) — essenziale perché Draco e HLS funzionino;
- serve `/mux/…` come HLS locale al posto di `stream.mux.com`;
- risponde a `/_a/…` con uno script vuoto + 204 (analytics neutralizzata);
- gestisce `/api/mux-image/…` con fallback per i poster non mirrorati.

---

## 9. Note per il rebranding (shader.se → BZN15)

Tre dipendenze di terze parti sono già state rese locali e i bundle patchati
(con gli originali conservati come `*.orig` / `*.bak_rebrand`):

| Era (terza parte) | Ora (locale) |
|---|---|
| `stream.mux.com` (video HLS) | `/mux/*.m3u8` + `.ts` |
| `www.gstatic.com` (decoder Draco) | `/draco/` |
| `analytics.shader.build` (Umami) | `/_a/` (no-op) |

I metadati (`<title>`, OpenGraph, Twitter card, `canonical` → `bzn15.it`) sono
già aggiornati al brand BZN15. Il file `REBRAND_CHECKLIST.md` traccia lo stato
del rebranding.
