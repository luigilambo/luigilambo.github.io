# shader.se — fully independent local mirror

A complete, self-contained copy of **https://www.shader.se/** that runs with
**zero third-party requests**. It is the *real* site — the original Next.js
HTML, every `_next` JS/CSS bundle (the real React-Three-Fiber + WebGL shader
code), the real Draco-compressed 3D models, textures, fonts, the CRT boot
screen — plus every Mux video downloaded locally and the bundles re-pointed at
local paths.

## Run it

```bash
cd mirror
python3 serve.py
# open http://127.0.0.1:8300
```

Verified: a full page load issues **93 requests, all to 127.0.0.1 — none external.**

## Made independent

Three things used to load from third parties; all are now local:

| Was (third party)                         | Now (local)            | How |
|-------------------------------------------|------------------------|-----|
| `stream.mux.com` HLS video                | `/mux/<id>.m3u8` + `.ts` | 53 videos pulled with `ffmpeg` into multi-segment HLS; bundle patched |
| `www.gstatic.com` Draco decoder           | `/draco/`              | decoder files downloaded; bundle patched |
| `analytics.shader.build` (Umami)          | `/_a/` (no-op)         | bundle patched; server returns empty script + 204 |

The patched file is `_next/static/chunks/0nr6lqdt2xw72.js` (and the analytics
ref in `index.html`). Originals are kept alongside as `*.orig`.

`serve.py` (threaded) handles: stripping the `?dpl=` query, HLS/`.ts`/`.wasm`
MIME types, the `/_a` analytics no-op, and the `/api/mux-image` poster fallback.

## What works
- CRT **boot screen** (real WebGL shader)
- 3D **hero** — beige PET computer with the **video playing inside the screen**
- The whole **scroll narrative** (desk scene, shredder, golden-tie, bank …)
- **Selected Work** carousel (videos + posters), **About**, **Contact / footer**

Everything runs offline. (The very first load still benefits from a connection
only if you ever clear `/mux` — otherwise no network is touched.)

## Layout
```
mirror/
├── serve.py                # local server (port 8300, threaded)
└── mirror_root/            # served site root
    ├── index.html
    ├── _next/…             # real JS/CSS bundles (patched: mux/draco/analytics → local)
    ├── models/*.glb        # 3D models
    ├── textures/…          # textures, icons, boot screen
    ├── fonts/…             # STIX typeface atlases
    ├── draco/…             # Draco decoder (was gstatic)
    ├── mux/…               # 53 videos as local HLS (was stream.mux.com)
    ├── videos/prebaked/…   # AVIF sprite-sheet fallback clips
    └── api/mux-image/…     # project carousel posters
```
