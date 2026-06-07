# Checklist rebranding Shader → bzn15

> Mirror root: `/Users/luigilambo/Desktop/test/mirror/mirror_root/`
> File doc/server: `/Users/luigilambo/Desktop/test/mirror/` (parent: `serve.py`, `README.md`)
> Nota tecnica: `index.html` è minificato su una riga e il JSON-LD è **duplicato** (versione `<script>` resa + versione escape `\"` nel payload RSC). Ogni modifica al JSON-LD va applicata a **entrambe le copie**.

---

## 1. Testi e contenuti
*(nome studio, tagline, copy, copyright, meta/title)*

| Cosa cambiare | Dove (file) | Valore attuale | Azione consigliata | Diff. |
|---|---|---|---|---|
| Nome studio "Shader Development Studio" (14 occorrenze: `<title>`, `og:title`, `og:site_name`, `twitter:title`, JSON-LD `name` Organization+WebSite) | `mirror_root/index.html` | `Shader Development Studio` | Sostituire ovunque con il nome brand bzn15 | 🟢 |
| `company.name` nel bundle dati | `mirror_root/_next/static/chunks/09d2g3rtnbzgs.js` | `name:"Shader Development Studio"` | Rinominare in bzn15 | 🟢 |
| Logo/home button (testo + aria-label) | `mirror_root/index.html` nav header | aria-label `Shader logo, go to home page` / testo `Shader — Home` | Sostituire "Shader" con bzn15 in aria-label e testo visibile | 🟢 |
| Copy "About" che nomina il brand (3 paragrafi) | `mirror_root/index.html` sezione about | "**Shader** is a creative development studio…"; "…**Shader** bridges the gap…"; "At **Shader**, we engineer success…" | Sostituire "Shader" → bzn15 nei tre paragrafi | 🟢 |
| Stesso copy about nel bundle dati (2 stringhe lunghe) | `mirror_root/_next/static/chunks/09d2g3rtnbzgs.js` | "Shader is a creative development studio…"; "Shader bridges the gap…" | Sostituire "Shader" → bzn15 in entrambe le stringhe | 🟢 |
| Meta description / `og:description` / `twitter:description` (stessa stringa 3x) + `tagline` nel bundle | `mirror_root/index.html` + `09d2g3rtnbzgs.js` | "Empowering Your Business with Next-Generation Interactive 3D and AI Solutions. Based in Sweden…" | Nessun token "Shader" letterale, ma è il positioning: riscrivere per voce bzn15 (e rimuovere "Sweden" se la sede cambia) | 🟢 |
| Hero H1 + sub-text | `mirror_root/index.html` hero | H1 "A Creative Development Studio, Plugged into the Future" / "Scroll to Inspect Our Closed Deals" | Copy di brand senza token letterale: mantenere o riscrivere per bzn15 | 🟢 |
| About H2 | `mirror_root/index.html` about | "Making Digital Storytelling More Playful, Powerful, and Alive" | Copy di brand: mantenere o riscrivere | 🟢 |
| JSON-LD `legalName` | `mirror_root/index.html` (reso + escape) + `09d2g3rtnbzgs.js` | `Shader Sweden AB` | Sostituire con ragione sociale registrata di bzn15 | 🟢 |
| JSON-LD `taxID` | `mirror_root/index.html` (2x) + `09d2g3rtnbzgs.js` | `5593233140` | Sostituire con P.IVA/cod. fiscale bzn15 (confermare se l'entità cambia) | 🟢 |
| JSON-LD `alternateName` | `mirror_root/index.html` WebSite (reso + escape) | `["Shader","Shader Sweden"]` | Sostituire con alias bzn15 | 🟢 |
| JSON-LD `Place.name` + `foundingLocation` | `mirror_root/index.html` Organization location | Place `Shader Sweden AB` / foundingLocation `Norrköping, Sweden` | Sostituire Place name con ragione sociale bzn15; aggiornare foundingLocation se la sede cambia | 🟢 |
| JSON-LD WebSite/Service `description` | `mirror_root/index.html` | "Creative development studio specialized in interactive 3D and AI solutions." / "Interactive 3D experiences, AI solutions…" | Copy positioning senza token: rivedere per bzn15 | 🟢 |
| Canonical / `og:url` (meta head) | `mirror_root/index.html` head | `https://www.shader.se` | Sostituire dominio → bzn15.it *(vedi §8 per il rename globale)* | 🟢 |

> Nota correttiva auditor: **NON esiste** una riga di copyright "Shader Development Studio AB, 2026" né il claim "A High Tech Business Solutions Company" dentro `index.html`. Quei testi vivono solo nelle immagini boot/footer (vedi §4). L'unico "2024" presente è in una case study (ICA), non un copyright.

---

## 2. Contatti e link
*(email, indirizzo, social, Cal.com)*

| Cosa cambiare | Dove (file) | Valore attuale | Azione consigliata | Diff. |
|---|---|---|---|---|
| Email generale `hello@shader.se` (mailto, testo, aria-label, JSON-LD ContactPoint+Organization.email — ~7 occorrenze, reso + escape) | `mirror_root/index.html` | `hello@shader.se` | Sostituire con `info@bzn15.it` ovunque (href, testo, aria-label, JSON-LD) | 🟢 |
| Email CEO `ceo@shader.se` (mailto, 2x testo, aria-label) | `mirror_root/index.html` Contact | `ceo@shader.se` | Sostituire con email business bzn15 | 🟢 |
| Set email nel bundle dati (general/ceo/**secretary**) | `mirror_root/_next/static/chunks/09d2g3rtnbzgs.js` | `hello@`, `ceo@`, `secretary@shader.se` | Sostituire tutte e tre. ⚠️ `secretary@shader.se` esiste **solo** qui (non in index.html) | 🟢 |
| Indirizzo ufficio (visibile + JSON-LD PostalAddress) | `mirror_root/index.html` `<address>` + JSON-LD | `Laxholmstorget 3 / 602 21 Norrköping / Sweden` (SE) | Sostituire con indirizzo bzn15 in entrambi i punti | 🟢 |
| Cal.com booking (3x in index.html + 1x bundle `call:`) | `mirror_root/index.html` (nav, hero CTA, Contact) + `09d2g3rtnbzgs.js` | `https://cal.com/simon-hedlund-kglzne` | Sostituire lo slug personale con il link booking bzn15. ⚠️ La CTA hero ha anche aria-label "Book a call **with Shader** on Cal.com" → cambiare anche il token "Shader" | 🟢 |
| Social `@shadersweden` LinkedIn/Instagram/X (URL + aria-label + JSON-LD sameAs — 9 occorrenze) | `mirror_root/index.html` | `linkedin.com/company/shadersweden/`, `instagram.com/shadersweden/`, `x.com/shadersweden` | Sostituire i 3 URL e il token "Shader" negli aria-label ("Shader on LinkedIn/Instagram/X") | 🟢 |
| Stessi 3 social nel bundle dati | `mirror_root/_next/static/chunks/09d2g3rtnbzgs.js` `social:{}` | linkedin/twitter/instagram `shadersweden` | Sostituire con gli handle bzn15 | 🟢 |

---

## 3. Logo e marchio grafico
*(SVG logo, favicon)*

| Cosa cambiare | Dove (file) | Valore attuale | Azione consigliata | Diff. |
|---|---|---|---|---|
| Logo SVG wordmark "SHADER" + disco rigato — tema chiaro | `mirror_root/_next/static/media/logo.0ctv.ko5~mr~7.svg` | Wordmark "SHADER" bianco serif + disco a 7 bande (#66C5F1 #D772EC #F64F39 #FA9D2E #FFCE43 #1DCDA1 #398AC7), viewBox 0 0 1285 173 | Sostituire l'intero SVG con wordmark "bzn15" + nuovo brand mark. ⚠️ Il filename ha un content-hash: cambierà se rigenerato dal build → aggiornare i riferimenti | 🟡 |
| Logo SVG variante scura | `mirror_root/_next/static/media/logo_dark.0a~p9g3zi7_h6.svg` | Stesso artwork, wordmark `#312F2B` per sfondi chiari, viewBox 0 0 306 41 | Sostituire con variante scura del nuovo logo bzn15 | 🟡 |
| Favicon SVG (solo disco rigato) | `mirror_root/icon.svg` | Solo brand mark a disco, 7 colori, viewBox 0 0 64 64 | Sostituire con nuova icona bzn15 | 🟡 |
| Riferimenti favicon nell'head + `favicon.ico` da rigenerare | `mirror_root/index.html` head (`favicon.ico` 256x256, `/icon.svg`, `/apple-icon.png`) | path `/favicon.ico…`, `/icon.svg`, `/apple-icon.png` | Rigenerare i binari da nuovo mark bzn15 (i path restano). ⚠️ `favicon.ico` è referenziato ma **non presente** su disco nel mirror: va comunque ricreato | 🟡 |
| Logo/OG image URL nel JSON-LD | `mirror_root/index.html` Organization | logo `https://www.shader.se/dark-colored.png`, image `https://www.shader.se/og` | Sostituire con asset bzn15-hosted e bzn15-branded (dominio coperto in §8, ma l'immagine logo va anche ri-renderizzata) | 🟡 |
| OG/Twitter share image (Prismic repo "shader", 4 occorrenze: og:image, twitter:image, JSON-LD image) | `mirror_root/index.html` head | `https://images.prismic.io/shader/aXyIqgIvOtkhCHKr_og.jpg…` | Ri-puntare a una share image bzn15-branded. Lo slug repo Prismic `shader` è un riferimento brand → probabile nuovo repo/asset | 🟡 |

---

## 4. Boot screen CRT
*(immagini con "SHADER" + testo nel bundle)*

| Cosa cambiare | Dove (file) | Valore attuale | Azione consigliata | Diff. |
|---|---|---|---|---|
| Boot screen CRT desktop | `mirror_root/textures/boot_screen.png` (720x404) | Disco + wordmark "SHADER", testo "Shader Development Studio, Website / Version 1.02" e "Copyright (c) Shader Development Studio AB, 2026. All Rights Reserved." | Ricreare il PNG: logo bzn15 + sostituire tutte le stringhe "Shader Development Studio"/copyright | 🟡 |
| Boot screen CRT mobile | `mirror_root/textures/boot_screen_mobile.png` (360x274) | Disco + wordmark "SHADER", "Shader Development Studio / Version 1.02", "Copyright (c) Shader Sweden AB, 2026…" | Ricreare il PNG con logo/testo bzn15 | 🟡 |
| Footer copyright lockup | `mirror_root/textures/copyright_footer.png` (1032x288, bianco su trasparente) | Disco + wordmark "SHADER", tagline "A High Tech Business Solutions Company", "© Shader Sweden AB. All Rights Reserved." | Ricreare PNG con logo bzn15, tagline opzionale, "© bzn15…". Mantenere bianco-su-trasparente per il footer scuro | 🟡 |

> ⚠️ Le stringhe di copyright/tagline che il brief si aspettava in HTML vivono **qui, dentro queste immagini** (e nei boot text), non come testo HTML.

---

## 5. Modello 3D del computer
*(label "SHADER" on-screen)*

| Cosa cambiare | Dove (file) | Valore attuale | Azione consigliata | Diff. |
|---|---|---|---|---|
| Texture schermo/badge del computer 3D | `mirror_root/models/computer.glb` — immagine embedded idx 2 `commodore-shader` (webp 1024x415), material `commodore-logo`, nodo `logo` | Disco + wordmark "SHADER", pannello boot "WELCOME TO FARMTIDEN", badge "SuperPET SP9000™" | Ri-autorare la webp (SHADER → bzn15; aggiornare/sostituire badge SuperPET e pannello FARMTIDEN se desiderato) e ri-pacchettizzare il GLB (Draco/EXT_texture_webp). Opz. rinominare image/material per pulizia | 🔴 |

---

## 6. Foto del team / persone reali

> Tutte in `mirror_root/textures/`. Sono persone Shader reali e identificabili → sostituire con membri team bzn15 (o rimuovere se non c'è equivalente).

| Cosa cambiare | Dove (file) | Valore attuale | Azione consigliata | Diff. |
|---|---|---|---|---|
| Jacob (presenting) | `mirror_root/textures/jacob_presenting.webp` | Foto reale (91 KB) | Sostituire con foto team bzn15 | 🟡 |
| Simon (presenting) | `mirror_root/textures/simon_presenting.webp` | Foto reale (76 KB). ⚠️ È l'owner del Cal.com `simon-hedlund-kglzne` (vedi §2) | Sostituire con foto team bzn15 | 🟡 |
| Simon (calling) | `mirror_root/textures/simon_calling.webp` | Foto reale (44 KB) | Sostituire con foto team bzn15 | 🟡 |
| Filip (footer) | `mirror_root/textures/filip_footer_5.webp` | Foto reale (101 KB) | Sostituire con foto team bzn15 | 🟡 |
| Jake (at computer) | `mirror_root/textures/jake_computer.webp` | Foto reale (46 KB) | Sostituire con foto team bzn15 | 🟡 |
| Simon (footer) — 6ª foto extra | `mirror_root/textures/simon_footer.webp` | Stesso Simon, variante footer (36 KB). ⚠️ Il file è in realtà HTML/testo con estensione errata e contiene markup brand duplicato; **non è referenziato** da alcun HTML/JS live (non servito) | Non servito → non bloccante. Sostituire/rimuovere per completezza ed evitare stringhe brand stantie se mai esposto | 🟡 |

---

## 7. Portfolio / video dei progetti (Selected Work)

| Cosa cambiare | Dove (file) | Valore attuale | Azione consigliata | Diff. |
|---|---|---|---|---|
| Dataset portfolio (11 progetti client reali) — array `projects` + JSON-LD `Portfolio` ItemList (`numberOfItems:11`) | `mirror_root/index.html` (payload RSC inline + JSON-LD duplicato) | 11 progetti: eHealth Arena, Select Concept, Gamily, Alamance Foods, Norrköpings Symfoniorkester, Glasbolaget, SPP Dream Generator, ICA-nissen, Norrköpings Hamn, HEIP, Design is Funny. Ogni voce: title, subtitle, `site_link` URL client, collaboratore, descrizione, `mux_playback_ids` | Sostituire l'intero dataset con i progetti bzn15: titoli, descrizioni, URL client esterni, crediti collaboratori (Markus Reklambyrå, Jungle Design, Wenderfalck, Daniele Buffa), e tutti i mux ID. Aggiornare anche i nomi/URL nella ItemList JSON-LD | 🔴 |
| URL case study `/work/<slug>` (11) | `mirror_root/index.html` — JSON-LD ItemList | `https://www.shader.se/work/{ehealth-arena, select-concept, gamily, alamance-foods, son, glasbolaget, spp-dream-generator, ica-nissen, norrkopings-hamn, heip, design-is-funny}` | Rimpiazzare slug e dominio con i progetti/URL bzn15 *(il dominio è coperto dal rename §8, ma gli slug vanno ridefiniti)* | 🔴 |
| Video progetti — playlist HLS locali (53 file) | `mirror_root/mux/*.m3u8` (referenziati dai `mux_playback_id` in index.html) | 53 playlist Mux = video client/showreel reali Shader (hero + gallery degli 11 progetti; alcuni ID ripetuti). Es. `Y7HzOsrmhjd7M00Ib6JYF861ME00I3ZqicLcr4V9vhoXU.m3u8` = eHealth Arena hero | Sostituire tutti i 53 asset con footage bzn15 e ri-puntare i `mux_playback_id` in index.html. Sono deliverable client reali: non possono uscire sotto rebrand | 🔴 |
| Decals logo "SHADER" sui telefoni 3D (3 istanze) | `mirror_root/models/phones.glb` — image idx 2 `shader-logo` (webp 1024x290), material `shader-logo`, nodi `phone-1/2/3-logo` | Disco + wordmark "SHADER" come decal su 3 telefoni | Sostituire la webp embedded con decal bzn15 e ri-pacchettizzare (una texture guida tutti e 3) | 🔴 |
| Decal logo "SHREDDER" stile-Shader | `mirror_root/models/shredder.glb` — image idx 1 `shredder-logo` (webp 1024x290), material `shader-logo`, nodo `cogs` | Disco + wordmark "SHREDDER" nello stile esatto del brand Shader | Ri-autorare la webp nello stile bzn15 (o rilavorare il disco così da non leggersi come mark Shader) e ri-pacchettizzare | 🔴 |

---

## 8. Domini e codice
*(shader.se, shader.build, analytics, ecc.)*

| Cosa cambiare | Dove (file) | Valore attuale | Azione consigliata | Diff. |
|---|---|---|---|---|
| Dominio `shader.se` (53 occorrenze: canonical, og:url, twitter, JSON-LD `@id`/`url`, 11 URL `/work/`, base og-image, `dark-colored.png`) | `mirror_root/index.html` | `https://www.shader.se` (+ `/work/<slug>`, `/og…`, `/dark-colored.png`) | Sostituire ogni host con `bzn15.it` (o dominio scelto). Copre meta, JSON-LD e i path immagine/OG | 🟢 |
| Dominio `shader.se` nel bundle dati (4 occorrenze: host email + `secretary@…` string) | `mirror_root/_next/static/chunks/09d2g3rtnbzgs.js` | `shader.se` | Sostituire con il dominio bzn15 ovunque sia host email/sito | 🟢 |
| Umami `data-website-id` (account analytics Shader) | `mirror_root/index.html` — config loader Umami | `9f3f6f74-e5fd-4290-b41f-5a4a64d5ec22` | Non è una stringa "shader" ma è il site-ID brand: sostituire con il website-id bzn15 o rimuovere. Lo script remoto era già patchato a `/_a/script.js` (no-op) | 🟢 |
| Docstring/commento server | `mirror/serve.py` (dir parent, **non** mirror_root) — docstring riga 2, commento riga 8 | "Static server for the fully-independent shader.se mirror." / "(replaces analytics.shader.build)" | Aggiornare wording brand → bzn15. Solo lato server, bassa priorità | 🟢 |
| README | `mirror/README.md` (dir parent) — riga 1, 3, 28 | "# shader.se — fully independent local mirror", "copy of https://www.shader.se/", "analytics.shader.build (Umami)" | Aggiornare wording brand → bzn15. Solo doc, bassa priorità | 🟢 |

> **Non toccare (non sono brand / sono patch volute):**
> - Path locali introdotti per l'indipendenza: `/_a/` (analytics no-op), `/mux/`, `/draco/` — puntano al mirror locale, non sono stringhe brand.
> - `shader.build` **non** esiste in nessun file live; sopravvive solo in `serve.py`, `README.md` e nei backup `*.orig` (non serviti), che descrivono l'host analytics già patchato.
> - Tutto l'uso tecnico WebGL/GLSL di "shader" (`vertexShader`, `fragmentShader`, `ShaderMaterial`… in `0nr6lqdt2xw72.js`) è escluso: non è brand.
> - Logo terzi non-Shader: `textures/customers_logo_cloud.png` (ICA, Pepsi, RISE…), badge tastiera `commodore 64` in computer.glb, `textures/footer_certificate.png` (badge globo generico), `textures/a11y-statement.png`. Nessun mark Shader.

---

## Priorità consigliata

1. **Testi/dominio/contatti in `index.html` + bundle `09d2g3rtnbzgs.js`** (§1, §2, §8) — 🟢 massimo impatto, minimo sforzo. Sono le stringhe brand visibili e SEO (title, meta, JSON-LD su **entrambe** le copie, email `info@bzn15.it`, indirizzo, social, Cal.com, rename `shader.se` → `bzn15.it`).
2. **Logo e favicon SVG** (§3) — 🟡 identità visiva primaria; sblocca poi boot screen e GLB.
3. **Boot screen CRT + footer lockup** (§4) — 🟡 contengono le uniche stringhe di copyright/legal entity in forma immagine.
4. **Foto team** (§6) — 🟡 persone reali identificabili, rischio immagine/privacy.
5. **Portfolio: dataset + URL `/work/` + 53 video Mux** (§7) — 🔴 lavoro client reale; non deve uscire sotto rebrand (priorità legale alta anche se sforzo alto).
6. **Texture nei GLB** computer / phones / shredder (§5, §7) — 🔴 ultimi, richiedono unpack/repack GLB (Draco + EXT_texture_webp).
7. **Doc server/README** (§8) — 🟢 last, solo interno/non user-facing.