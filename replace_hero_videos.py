#!/usr/bin/env python3
"""Sostituisce i due video dello schermo del SuperPET (hero) con un montaggio
dei nuovi video servizio BZN15 — gli originali erano lo showreel del progetto
shader "Design is Funny".

I due id sono HARDCODED nel bundle (funzione O8, vedi ANALISI_VIDEO_HERO.md),
quindi come per i servizi si riconverte SOPRA gli stessi id:
  - S6lqlADo… : schermo dritto,   640x480 (4:3)
  - bGeuEyty… : riflesso/glow, 320x240 ruotato 180° (hflip+vflip, come l'orig)

Montaggio: CLIP_LEN secondi da ciascun video in CLIPS (offset scelto da
best_window: la finestra col luma medio piu' basso, vedi sotto) — durata
complessiva vicina al loop originale shader (12.87 s).
Idempotente; backup one-shot in mux_backup_shader/<id>/.
"""
import os, glob, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MUX = os.path.join(HERE, "mirror_root", "mux")
BACKUP = os.path.join(HERE, "mux_backup_shader")
VIDEO_DIR = os.path.join(os.path.dirname(HERE), "video")

# Ordine = carosello servizi, MENO Cybersecurity e Infrastrutture e Cloud
# (clip troppo scuri, stonano coi toni degli altri — scelta utente, fase 7).
# 6 clip da 2 s = loop di 12 s, come il ~12.9 s dell'originale shader.
CLIPS = [
    "Sviluppo_software_e_SaaS.mp4", "Governance_rischio_e_conformita.mp4",
    "Reti e Telecomunicazioni.mp4", "Gestione_di_sistemi_e_applicazioni.mp4",
    "Impiantistica_tecnologica.mp4", "Formazione_e_Consulenza.mp4",
]
CLIP_LEN = 2.0

# Lo schermo del SuperPET ha un bloom/glow additivo nel materiale 3D: i bianchi
# pieni del video saturano l'effetto e impastano il contenuto (es. lo schermo
# di proiezione del clip Formazione). Comprimiamo le alte luci direttamente nel
# montaggio: toni medi leggermente giu', picco bianco a ~62%.
TONE = "curves=all='0/0 0.55/0.45 1/0.62'"
HERO = [
    # (playback id, larghezza, altezza, ruotato 180°)
    ("S6lqlADoaaT2Di8G201LyzNktQSKPBnNjWPNJLHkghQA", 640, 480, False),
    ("bGeuEyty7wU5FEfMe66HTfceuHj8RDamdu8BdHLAD01I", 320, 240, True),
]

def best_window(src, clip_len=1.6):
    """Offset (s) della finestra di clip_len col luma medio PIU' BASSO.
    Le inquadrature dominate dal bianco (editor, schermi di proiezione)
    saturano il bloom dello schermo 3D: meglio i momenti scuri del clip."""
    r = subprocess.run(["ffprobe", "-v", "error", "-f", "lavfi",
                        "-i", f"movie='{src}',fps=2,signalstats",
                        "-show_entries", "frame_tags=lavfi.signalstats.YAVG",
                        "-of", "csv=p=0"], capture_output=True, text=True)
    ys = [float(x.rstrip(",")) for x in r.stdout.split() if x.rstrip(",")]
    if len(ys) < 4:
        return 0.0
    w = max(1, int(clip_len * 2))                    # campioni a 2 fps
    last = len(ys) - w - 1                           # margine di coda
    means = [(sum(ys[i:i + w]) / w, i) for i in range(0, max(1, last))]
    return min(means)[1] / 2.0

def backup(pid):
    dst = os.path.join(BACKUP, pid)
    if os.path.isdir(dst):
        return
    os.makedirs(dst)
    for f in [os.path.join(MUX, pid + ".m3u8")] + sorted(glob.glob(os.path.join(MUX, pid + "_*.ts"))):
        shutil.copy2(f, dst)

def main():
    offsets = {}
    for name in CLIPS:
        src = os.path.join(VIDEO_DIR, name)
        assert os.path.isfile(src), f"manca {src}"
        offsets[name] = best_window(src, CLIP_LEN)
        print(f"  finestra meno luminosa: {name:42} t={offsets[name]:.1f}s")
    for pid, w, h, flip in HERO:
        backup(pid)
        for f in glob.glob(os.path.join(MUX, pid + "_*.ts")):
            os.unlink(f)
        args = ["ffmpeg", "-y"]
        fc = []
        for i, name in enumerate(CLIPS):
            src = os.path.join(VIDEO_DIR, name)
            args += ["-ss", f"{offsets[name]:.2f}", "-t", f"{CLIP_LEN}", "-i", src]
            fc.append(f"[{i}:v]crop=min(iw\\,ih*4/3):min(ih\\,iw*3/4),"
                      f"scale={w}:{h}:flags=lanczos,fps=30,setsar=1[v{i}]")
        rot = ",hflip,vflip" if flip else ""
        fc.append("".join(f"[v{i}]" for i in range(len(CLIPS)))
                  + f"concat=n={len(CLIPS)}:v=1:a=0,{TONE}{rot}[out]")
        args += ["-filter_complex", ";".join(fc), "-map", "[out]", "-an",
                 "-c:v", "libx264", "-preset", "medium", "-crf", "22",
                 "-pix_fmt", "yuv420p",
                 "-force_key_frames", "expr:gte(t,n_forced*2)",
                 "-f", "hls", "-hls_time", "2", "-hls_playlist_type", "vod",
                 "-hls_list_size", "0",
                 "-hls_segment_filename", pid + "_%03d.ts", pid + ".m3u8"]
        r = subprocess.run(args, capture_output=True, text=True, cwd=MUX)
        if r.returncode != 0:
            sys.exit(f"FFMPEG FAIL [{pid}]:\n{r.stderr[-1500:]}")
        nseg = len(glob.glob(os.path.join(MUX, pid + "_*.ts")))
        size = sum(os.path.getsize(f) for f in glob.glob(os.path.join(MUX, pid + "_*.ts"))) // 1024
        print(f"[{pid[:20]}…] {w}x{h}{' 180°' if flip else ''}  seg={nseg} {size}KB")
    print("done.")

if __name__ == "__main__":
    main()
