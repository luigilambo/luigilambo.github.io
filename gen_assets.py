#!/usr/bin/env python3
"""Fase 4 — generazione asset mancanti (idempotente).

  1. w480-h360-fpreserve-t0 per OGNI dir api/mux-image/ (404 su iOS reducedMemory):
     resize 480x360 dalla sorgente 800x600 esistente (h640* o w800*).
  2. w1200-h630-fsmartcrop per gli id og delle 8 pagine work (cover+center-crop).
  3. og.jpg home 1200x630 brandizzata BZN15 (+ copia in dark-colored.png per il logo
     JSON-LD).
  4. boot_screen.png -> quantizzazione 256 colori (asset sul percorso critico).
  5. pulizia: 'copyright_footer copia.png', .DS_Store.

Va girato fuori dal sandbox del tool (lettura/scrittura su mirror_root).
"""
import os, glob, re
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "mirror_root")
MUX = os.path.join(ROOT, "api", "mux-image")
TEX = os.path.join(ROOT, "textures")

def source_for(d):
    for v in ("w800-h600-fpreserve-t0", "h640-fpreserve-t0"):
        p = os.path.join(d, v)
        if os.path.exists(p):
            return p
    # qualunque file immagine presente
    for f in os.listdir(d):
        return os.path.join(d, f)
    return None

def gen_w480():
    n = 0
    for d in sorted(glob.glob(os.path.join(MUX, "*"))):
        if not os.path.isdir(d):
            continue
        out = os.path.join(d, "w480-h360-fpreserve-t0")
        if os.path.exists(out):
            continue
        src = source_for(d)
        if not src:
            print("  ! nessuna sorgente in", os.path.basename(d)); continue
        im = Image.open(src).convert("RGB").resize((480, 360), Image.LANCZOS)
        im.save(out, format="JPEG", quality=82)
        n += 1
    print(f"  w480-h360: {n} generate")

def cover_crop(im, w, h):
    sw, sh = im.size
    scale = max(w / sw, h / sh)
    im = im.resize((round(sw * scale), round(sh * scale)), Image.LANCZOS)
    nw, nh = im.size
    left, top = (nw - w) // 2, (nh - h) // 2
    return im.crop((left, top, left + w, top + h))

def gen_work_og():
    ids = set()
    for p in glob.glob(os.path.join(ROOT, "work", "*", "index.html")):
        html = open(p, encoding="utf-8").read()
        for m in re.finditer(r'api/mux-image/([^/"\\]+)/w1200-h630-fsmartcrop', html):
            ids.add(m.group(1))
    n = 0
    for i in sorted(ids):
        d = os.path.join(MUX, i)
        out = os.path.join(d, "w1200-h630-fsmartcrop")
        if os.path.exists(out):
            continue
        src = source_for(d)
        if not src:
            print("  ! niente sorgente og per", i); continue
        cover_crop(Image.open(src).convert("RGB"), 1200, 630).save(out, format="JPEG", quality=84)
        n += 1
    print(f"  w1200-h630 og work: {n} generate (su {len(ids)} id)")

def load_font(size):
    for f in ("/System/Library/Fonts/Helvetica.ttc",
              "/System/Library/Fonts/HelveticaNeue.ttc",
              "/System/Library/Fonts/Supplemental/Arial.ttf",
              "/Library/Fonts/Arial.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            pass
    return ImageFont.load_default()

def gen_og_home():
    out = os.path.join(ROOT, "og.jpg")
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), (13, 13, 15))
    dr = ImageDraw.Draw(img)
    # cornice sottile
    dr.rectangle([40, 40, W - 40, H - 40], outline=(60, 60, 66), width=2)
    big = load_font(150); small = load_font(40)
    def centered(text, font, y, fill):
        bb = dr.textbbox((0, 0), text, font=font)
        dr.text(((W - (bb[2] - bb[0])) / 2, y), text, font=font, fill=fill)
    centered("BZN15", big, 215, (245, 245, 245))
    centered("Sistemi informatici · Bari", small, 400, (160, 160, 168))
    img.save(out, format="JPEG", quality=88)
    # il logo JSON-LD punta a /dark-colored.png e /og.jpg: forniamo entrambi
    img.save(os.path.join(ROOT, "dark-colored.png"), format="PNG")
    print("  og.jpg + dark-colored.png creati")

def opt_boot_screen():
    p = os.path.join(TEX, "boot_screen.png")
    if not os.path.exists(p):
        print("  boot_screen.png assente, skip"); return
    before = os.path.getsize(p)
    im = Image.open(p)
    q = im.convert("RGBA").quantize(colors=256, method=Image.FASTOCTREE)
    q.save(p, format="PNG", optimize=True)
    after = os.path.getsize(p)
    print(f"  boot_screen.png: {before//1024}KB -> {after//1024}KB")

def cleanup():
    for f in [os.path.join(TEX, "copyright_footer copia.png"),
              os.path.join(ROOT, ".DS_Store")]:
        if os.path.exists(f):
            os.remove(f); print("  rimosso:", os.path.relpath(f, HERE))
    for dp, _, fns in os.walk(ROOT):
        for fn in fns:
            if fn == ".DS_Store":
                os.remove(os.path.join(dp, fn)); print("  rimosso DS_Store in", os.path.relpath(dp, HERE))

if __name__ == "__main__":
    print("[1] w480-h360");   gen_w480()
    print("[2] w1200-h630");  gen_work_og()
    print("[3] og.jpg home"); gen_og_home()
    print("[4] boot_screen"); opt_boot_screen()
    print("[5] pulizia");     cleanup()
    print("done.")
