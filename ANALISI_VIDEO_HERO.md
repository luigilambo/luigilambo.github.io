# Analisi — Video della hero nel modello SuperPET ("schermo nero")

> **Domanda di partenza:** perché i video dentro al modello 3D del computer
> SuperPET, nella hero, "non partono" e lo schermo resta nero?
>
> **Verdetto breve:** la pipeline video **è integra e funziona** (verificato
> empiricamente su Chrome + `serve.py`: i video decodificano frame e lo schermo
> mostra il filmato). Il "nero" percepito è quasi sempre uno di questi:
> (a) il **frame iniziale freddo/ciano** per ~1–2 s prima che arrivi il contenuto;
> (b) l'**autoplay bloccato senza gesto utente** su Safari/iOS (low MEI / Low
> Power Mode), che lascia la VideoTexture sul primo frame nero senza errori in
> console. Gli asset in produzione sono integri; il deploy **non** è la causa.

| | |
|---|---|
| **Data analisi** | 2026-06-08 / 2026-06-09 |
| **Metodo** | run locale (`serve.py` :8300) + Chrome DevTools (console, network, pixel-readback, screenshot) + review multi-agente (6 specialisti + 6 verifiche avversariali) |
| **Bundle rilevante** | `mirror_root/_next/static/chunks/0nr6lqdt2xw72.js` (minificato; contiene `Ow`, `O5`, `O8`, la classe HLS.js `O_`) |
| **Stato pipeline** | ✅ funzionante in Chrome locale; rischi latenti + gap cross-browser documentati sotto |

---

## 1. Anatomia della pipeline video

Lo schermo del SuperPET (`mirror_root/models/computer.glb`) mostra video **Mux in
HLS** come `THREE.VideoTexture`, dentro l'unico canvas WebGL React-Three-Fiber.

Funzioni chiave nel bundle `0nr6lqdt2xw72.js`:

- **`Ow({src, signal, options})`** — funzione async di basso livello. Crea un
  `<video>` *detached*, imposta `playsinline`/`webkit-playsinline`, e se
  `src.includes(".m3u8") && O_.isSupported()` aggancia HLS.js
  (`new O_; loadSource; attachMedia`), altrimenti `video.src = src` (HLS nativo /
  mp4). Costruisce la `VideoTexture`, risolve su `loadeddata`, poi `play()` se
  `start` è true. **Filtra già `AbortError`** correttamente (modello da imitare).
  Tiene una cache per `src` nella Map `OR`. Bookkeeping sulla texture:
  `_hls`, `_src`, `_preload`, `_abortController`; helper `OM` (warm:
  `_hls.startLoad(-1)`) e `OD` (teardown: `_hls.destroy()`).

- **`O5(src, {loop,muted,playsInline})`** — hook React. Crea `<video>` detached +
  `VideoTexture` (`SRGBColorSpace`). `useEffect`: se HLS → `new O_; loadSource;
  attachMedia; on(MANIFEST_PARSED → play().catch(()=>{}))`; altrimenti
  `video.src = src; on(loadeddata → play())`. **Nessun handler `Events.ERROR`,
  nessun retry, catch vuoti.** Istanza HLS salvata come `a.hls` (NON `_hls`).

- **`O8({renderHandle})`** — scena del computer. Carica `computer.glb` e crea
  **due** VideoTexture via `O5`:
  - `n = O5(offlineMode ? "/showreel.mp4" : "/mux/S6lqlADoaaT2Di8G201LyzNktQSKPBnNjWPNJLHkghQA.m3u8", …)`
  - `a = O5(offlineMode ? "/showreel.mp4" : "/mux/bGeuEyty7wU5FEfMe66HTfceuHj8RDamdu8BdHLAD01I.m3u8", …)`

  `offlineMode` viene da `usePerformanceStore` con **default `false`**
  (`offlineMode:!1`); nessun toggle UI trovato. Un `useEffect` con
  `setInterval(…, 1000ms)` + listener su `activePage`/`subPage` + `visibilitychange`
  esegue `r()`: se `activePage !== "hero" || subPage` → pause; altrimenti
  `await play()` in try/catch sui due video.

- Componente separato (scroll-triggered) usa
  `Ow({src:"/mux/o00A8B2OYj2sOcscmsp4TFsft9fqiOuhxg014y2E01Ea00o.m3u8", assetId:"business-man-papers", options:{autoplay:false, start:false, preload:"metadata"}})`
  — **volutamente in pausa** a t=0 (primo frame nero, 1518×1080). NON è lo schermo
  della hero; non va forzato in play.

**Asset Mux:** 53 `.m3u8` + 90 `.ts` in `mirror_root/mux/`, repuntati da
`stream.mux.com` a `/mux/` nel bundle. Codec verificati (ffprobe): **H.264 High,
8-bit yuv420p, BT.709**, dentro l'envelope hardware Safari/iOS. I codec **non**
sono la causa. Tutti i playlist sono single-rendition VOD (`#EXT-X-ENDLIST`,
niente `#EXT-X-STREAM-INF`, niente `#EXT-X-BYTERANGE`/`#EXT-X-MAP`).

---

## 2. Prova empirica (Chrome + serve.py)

Stato reale dei `<video>` letto da DevTools dopo il boot, in hero:

| Video | Playback ID | Stato | Frame |
|-------|-------------|-------|-------|
| Schermo 1 | `S6lqlADoaaT…` (640×480) | `paused:false`, `readyState:4` | 100+ decodificati, pixel **arancioni** [193,99,55] |
| Schermo 2 | `bGeuEyty7wU…` (320×240) | `paused:false`, `readyState:4` | 100+ decodificati, pixel **blu** [78,87,163] |
| Hero scroll | `o00A8B…` (1518×1080) | `paused:true` a t=0 | frame **nero** [0,0,0] — intenzionale |

Tutte le richieste `/mux/*.m3u8` e `/mux/*.ts` → **200** con MIME corretti. Lo
screenshot della hero mostra il filmato (mani/documenti) sullo schermo del
SuperPET. **Conclusione: i video partono.** Unico warning in console, transitorio
e auto-recuperato: `Slave video play failed on sync: AbortError: The play()
request was interrupted by a call to pause()`.

---

## 3. I due vincoli architetturali che decidono ogni soluzione

> Questi due fatti spiegano perché gli approcci "ovvi" falliscono. **Da leggere
> prima di proporre qualsiasi fix.**

1. **I `<video>` della hero sono DETACHED dal DOM.** Creati con
   `document.createElement('video')` in `O5`/`Ow` e mai inseriti nel documento
   (servono solo come sorgente `VideoTexture`). Conseguenze:
   - `document.querySelectorAll('video')` **non li trova** → ogni script che li
     enumera così è un **no-op**.
   - L'attributo HTML `poster` **non viene mai dipinto** (lo schermo è una
     `VideoTexture` campionata da WebGL, non un `<video>` visibile).
   - Per raggiungerli serve uno script che intercetti `document.createElement`
     (o patchi `HTMLMediaElement.prototype`) **prima** del caricamento del bundle.

2. **La classe HLS.js è module-scoped** (minificata come `O_`), **mai esposta su
   `window`/`self`/`globalThis`** (0 occorrenze). Conseguenze:
   - **Impossibile** da uno script iniettato: configurare HLS.js, avvolgere il
     costruttore, o aggiungere un handler `Events.ERROR`.
   - Config HLS e recovery fatale (`startLoad()`, `recoverMediaError()`)
     richiedono **per forza** una modifica al bundle (alto rischio).

Nota d'iniezione: `index.html` non ha CSP e carica il bundle con `async` → uno
`<script>` sincrono come primo elemento in `<head>` gira **prima** che `O5` crei
i video (lo stack iniettato è meccanicamente fattibile).

---

## 4. Teorie verificate e SMENTITE

| Teoria | Esito | Evidenza |
|--------|-------|----------|
| Asset video gitignorati → 404 in produzione | ❌ **Smentita** | 90 `.ts` + 53 `.m3u8` committati come byte reali (no LFS), 0 segmenti referenziati mancanti, entro i limiti Pages (mux 74M, sito 89M, file max 3.85M) |
| MIME `.m3u8` errato su GitHub Pages rompe Safari nativo | ❌ **Smentita** | L'HLS.js del bundle è moderno (`ManagedMediaSource`); `O_.isSupported()` è **true anche su Safari 17+/iOS** → **anche Safari usa HLS.js**, che fa fetch del manifest via XHR e parsing per contenuto (MIME-agnostico). Il path nativo `video.src=m3u8` non viene preso |
| Mancanza di Range/206 in `serve.py` → schermo nero | ⚠️ **Sovrastimata** | I segmenti sono VOD interi e minuscoli (1–2 `.ts`); HLS.js tollera 200-full-file. Range resta utile per seek Safari-nativo/mp4 e parità, ma **non** è la causa |
| Rebrand ha rotto la logica video | ❌ **Smentita** | Il commit rebrand tocca solo 3 stringhe di copy (`"Shader"→"BZN15"` in heading JSX) + repoint locali. `Ow`/`O5`/`O8` identici all'originale shader.se |

**Rischio reale in produzione invece confermato:** tutti i path sono
**root-absolute** (`/mux/…`, `/_next/…`); risolvono **solo** sul dominio apex
`bzn15.it` (CNAME + `.nojekyll` presenti). Se il custom domain cade (→
`user.github.io/repo/`) è **black screen totale**, non solo video.

---

## 5. Diagnosi della causa del "nero"

In ordine di probabilità per ciò che l'utente ha visto:

1. **Frame freddo iniziale (~1–2 s):** la `VideoTexture` non ha pixel finché non
   arriva il primo frame decodificato → ciano/nero. Identico in locale e in prod.
2. **Autoplay bloccato senza gesto** (Safari low Media Engagement Index, iOS Low
   Power Mode): i `play()` di `O5` hanno catch vuoti e nessun retry/unlock → lo
   schermo resta sul primo frame nero **senza errori in console**.
3. **Race play/pause** (`AbortError`): transitorio, auto-recupera, ma su rete
   lenta può lasciare un video in pausa su un frame freddo fino a ~1 s.
4. (Latente) **`offlineMode` → `/showreel.mp4` che è 404**: oggi inattivo
   (default false), ma se attivato entrambi gli schermi vanno neri.

---

## 6. Piano soluzioni (prioritizzato, post-verifica)

### Tier 1 — Alto impatto, basso rischio, nessuna modifica al bundle

Fondazione comune: **un solo `<script>` iniettato per primo in `<head>`** che
intercetta `createElement('video')` e mantiene un registro dei video detached.

- **1.1 — Wrapper `play()`**: coalescing per-elemento + swallow `AbortError`.
  Elimina il race del `setInterval` da 1 s e il warning in console.
- **1.2 — Sblocco autoplay al primo gesto** (`pointerdown`/`touchstart`/`keydown`/
  `wheel`/`scroll` → `play()` sui **due** video hero, **escluso** `o00A8B`).
  Copre Safari low-MEI e iOS Low Power Mode. Filtrare per src-id
  (`S6lqlADo`/`bGeuEyty`).
- **1.3 — Pausa su `visibilitychange` hidden** (resume lasciato al bundle).
  Stoppa il decode in background.
- **1.4 — Splash/poster DOM** che sfuma sul **primo frame reale**
  (`requestVideoFrameCallback`, cap di sicurezza ~8 s). Maschera il ciano freddo.
  ⚠️ Usare uno **splash brand neutro** (tinta + logo BZN15), **non**
  `boot_screen.png` a tutto schermo (coprirebbe l'intero modello 3D). Verificare
  prima se il boot-screen in-scena (`Gi`) copre già parte della finestra fredda.
- **1.5 — Aggiungere `mirror_root/showreel.mp4`** (remux verificato:
  `ffmpeg -i mux/S6lqlADo….m3u8 -c copy -movflags +faststart showreel.mp4`).
  Chiude il 404 latente di `offlineMode`. Deploy-safe (non gitignorato, non
  strippato).
- **1.6 — Warm-up rete in `<head>`**: `rel=preload as=fetch` (**non** `prefetch`,
  **senza** `crossorigin`, per deduplicare con la XHR same-origin di HLS.js) sui
  due manifest **e** sui primi segmenti fissi (`S6lqlADo…_000.ts` 1.33 MB,
  `bGeuEyty…_000.ts` 154 KB). −1/2 s sul time-to-first-frame. NON scaldare
  `o00A8B` (deve restare lazy).

### Tier 2 — Robustezza & parità (rischio basso)

**`serve.py`** (solo fedeltà dev locale; in prod Pages fa già tutto — NON cambia
la riproduzione già funzionante):
- Range/206 + `Accept-Ranges` via override di `send_head`.
  ⚠️ **Mantenere** la chiamata a `super().do_GET()` (le branch `/_a/` e
  `/api/mux-image/` ci passano). Streammare esattamente i byte del range.
- Split cache: `.m3u8` → `no-cache`; `.ts` → `max-age=86400`; **no `immutable`**
  su `.mp4` in dev (un re-remux di `showreel.mp4` resterebbe pinnato stale).
- MIME: l'unico realmente non mappato è `.glb` (`model/gltf-binary`) — peraltro
  cosmetico (GLTFLoader ignora il Content-Type). Le altre add_type erano ridondanti.
- `HTTP/1.1` opzionale: solo dopo aver garantito `Content-Length` esatto su ogni
  risposta, altrimenti il keep-alive desincronizza.

**Deploy** (severità reale in produzione):
- **Mantenere il dominio apex `bzn15.it`** configurato (path root-absolute).
- Restare su **commit-as-is**; mai mettere i media in **Git LFS** (Pages non
  risolve i pointer → 404).
- **Verifica live** post-deploy su `bzn15.it` in **Chrome e Safari** (Network:
  manifest + `.ts` = 200, schermo mostra video).
- **Estendere lo strip backup** del workflow a `*.bak_*`: oggi
  `index.html.bak_chisiamo` & co. **verrebbero pubblicati** (leak/igiene).

### Tier 3 — Solo se Tier 1 non basta (alto rischio, edita il bundle)

Unico modo per **config HLS.js + recovery fatale** (perché `O_` è module-scoped):
due edit chirurgici ai siti `new O_` in `O5` e `Ow`, aggiungendo
`r.on(O_.Events.ERROR, (x,d) => { if(!d.fatal) return;
if(d.type===O_.ErrorTypes.NETWORK_ERROR) r.startLoad();
else if(d.type===O_.ErrorTypes.MEDIA_ERROR) r.recoverMediaError();
else r.destroy(); })` (costanti enum, **non** stringhe) e una config `__HC`
(`maxBufferLength:10, backBufferLength:0, fragLoadingMaxRetry,
manifestLoadingMaxRetry`; ABR/`startLevel` inutili — single-rendition).
Bundle minificato/vendored: backup `.orig` + assert in CI che `function O5(` e
`O_.Events.ERROR` esistano post-build. Per il poster, **non** infilare un'immagine
fissa dentro `VideoTexture.image`; semmai seedare l'uniform `reelTexture` con il
`boot_screen` già caricato.

---

## 7. Rischi latenti (tabella)

| Rischio | Severità | Stato oggi | Fix |
|---------|----------|-----------|-----|
| Custom domain apex perso → path assoluti 404 | **Alta** (prod) | Mitigato (CNAME presente) | Tenere `bzn15.it` configurato |
| Autoplay bloccato senza gesto (Safari/iOS) | **Alta** (mobile) | Nessun unlock | Tier 1.2 |
| `/showreel.mp4` 404 se `offlineMode=true` | Media | Latente (default false) | Tier 1.5 |
| `*.bak_chisiamo` pubblicati in prod | Bassa | Untracked oggi | Tier 2 (strip `*.bak_*`) |
| Nessun recovery su errore HLS fatale | Media | Nessun handler | Tier 3 |
| Race play/pause (`AbortError`) | Bassa | Auto-recupera | Tier 1.1 |

---

## 8. Riferimenti file / anchor

- Bundle pipeline: `mirror_root/_next/static/chunks/0nr6lqdt2xw72.js`
  (`Ow`, `O5`, `O8`, classe HLS.js `O_`, store `usePerformanceStore` con
  `offlineMode:!1`).
- Server dev: `serve.py` (`SimpleHTTPRequestHandler`, no Range, HTTP/1.0,
  MIME `.m3u8`/`.ts`/`.wasm`, repoint `/_a/` `/api/mux-image/`).
- Asset: `mirror_root/mux/*.m3u8` + `*.ts`; `mirror_root/videos/prebaked/handshake_avif/`
  (fallback AVIF — clip *handshake*, non il reel SuperPET); `mirror_root/showreel.mp4`
  (DA CREARE).
- Deploy: `.github/workflows/deploy-pages.yml`, `mirror_root/CNAME` (`bzn15.it`),
  `mirror_root/.nojekyll`, `.gitignore`.
- Modello schermo: `mirror_root/models/computer.glb` (badge "SuperPET SP9000™",
  pannello "WELCOME TO FARMTIDEN", texture embedded `commodore-shader`).
- Contesto architetturale: `ARCHITETTURA.md` (§4.3 Video — Mux in HLS).
