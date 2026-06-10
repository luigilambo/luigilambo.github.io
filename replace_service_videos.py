#!/usr/bin/env python3
"""Sostituisce i video dei servizi (carosello home + hero delle pagine /work)
con gli MP4 BZN15 di Desktop/test/video, mantenendo i playback id Mux.

Strategia: i bundle e il flight referenziano i video SOLO per playback id
(/mux/<id>.m3u8 e /api/mux-image/<id>/...), quindi si riconvertono gli MP4 in
HLS locale SOPRA gli stessi id — zero modifiche a HTML/JS. Per ogni servizio:
  1. backup one-shot di m3u8+ts+poster originali in mux_backup_shader/<id>/
  2. MP4 -> HLS (h264 yuv420p, crf 22, segmenti da 2 s, naming <id>_NNN.ts)
     con crop CENTRALE a 4:3 (1440x1080): le card del carosello e i poster
     originali sono 4:3, i nuovi MP4 sono 16:9 — comportamento object-fit:cover
  3. rigenera i 3 poster JPEG in api/mux-image/<id>/ dal primo frame (t0):
     w480-h360-fpreserve-t0, w800-h600-fpreserve-t0 (4:3) e
     w1200-h630-fsmartcrop (ratio og 40:21, crop centrale dal 16:9 nativo)

Idempotente: il backup non viene sovrascritto; conversione e poster sì.
"""
import os, glob, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "mirror_root")
MUX = os.path.join(ROOT, "mux")
POSTERS = os.path.join(ROOT, "api", "mux-image")
BACKUP = os.path.join(HERE, "mux_backup_shader")
VIDEO_DIR = os.path.join(os.path.dirname(HERE), "video")

# servizio -> (file MP4, playback id del video principale della card)
VIDEOS = {
    "cybersecurity":
        ("Cybersecurity.mp4", "Y7HzOsrmhjd7M00Ib6JYF861ME00I3ZqicLcr4V9vhoXU"),
    "governance-rischio-e-conformita":
        ("Governance_rischio_e_conformita.mp4", "29xq00NijxLTofeMmyr1hvjJjStsZbMzzOBnP8JN24NM"),
    "infrastrutture-e-cloud":
        ("Infrastrutture_e_Cloud.mp4", "WR4ERwHNIF5rXY9l026yYwwacbpWgU7q3FrYxKYwqDrY"),
    "sviluppo-software-e-saas":
        ("Sviluppo_software_e_SaaS.mp4", "crXxuu5ds7W2UrGP1JE00V01xgtotSe02OOUojNBKjprKg"),
    "reti-e-telecomunicazioni":
        ("Reti e Telecomunicazioni.mp4", "hrfPaZr4FOpHh2iiUzTz01ppZApstkbjMH01vyZ5bDEg8"),
    "gestione-di-sistemi-e-applicazioni":
        ("Gestione_di_sistemi_e_applicazioni.mp4", "cUnrcyhPVk47A500005QHTfK00wUyr201vc2NEORq5ybaCE"),
    "impiantistica-tecnologica":
        ("Impiantistica_tecnologica.mp4", "JFKPwSwJdrTK6zn1c013dCw5HTxkekifCD8cbWWmd7JQ"),
    "formazione-e-consulenza":
        ("Formazione_e_Consulenza.mp4", "caSLneThURyYn402mCTXi6sgHLpL2F0201EcF01rI3ZwKk8"),
}

CROP43 = r"crop=min(iw\,ih*4/3):min(ih\,iw*3/4)"          # centrale, 4:3
CROPOG = r"crop=min(iw\,ih*40/21):min(ih\,iw*21/40)"      # centrale, 1200x630

def run(args, **kw):
    r = subprocess.run(args, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.exit(f"FFMPEG FAIL ({' '.join(args[:6])}…):\n{r.stderr[-1500:]}")

def backup(pid):
    dst = os.path.join(BACKUP, pid)
    if os.path.isdir(dst):
        return False
    os.makedirs(dst)
    for f in [os.path.join(MUX, pid + ".m3u8")] + sorted(glob.glob(os.path.join(MUX, pid + "_*.ts"))):
        shutil.copy2(f, dst)
    pd = os.path.join(POSTERS, pid)
    if os.path.isdir(pd):
        shutil.copytree(pd, os.path.join(dst, "posters"))
    return True

def main():
    for slug, (mp4, pid) in VIDEOS.items():
        src = os.path.join(VIDEO_DIR, mp4)
        assert os.path.isfile(src), f"manca {src}"
        b = backup(pid)
        # vecchi segmenti via (il numero di segmenti cambia)
        for f in glob.glob(os.path.join(MUX, pid + "_*.ts")):
            os.unlink(f)
        # MP4 -> HLS: cwd=mux così la playlist referenzia i bare name come l'orig
        run(["ffmpeg", "-y", "-i", src, "-an",
             "-c:v", "libx264", "-preset", "medium", "-crf", "22",
             "-maxrate", "8M", "-bufsize", "16M", "-pix_fmt", "yuv420p",
             "-vf", CROP43 + ",scale=1440:1080:flags=lanczos",
             "-force_key_frames", "expr:gte(t,n_forced*2)",
             "-f", "hls", "-hls_time", "2", "-hls_playlist_type", "vod",
             "-hls_list_size", "0",
             "-hls_segment_filename", pid + "_%03d.ts", pid + ".m3u8"],
            cwd=MUX)
        # poster dal primo frame del sorgente nativo
        pd = os.path.join(POSTERS, pid)
        os.makedirs(pd, exist_ok=True)
        for name, vf in [
            ("w480-h360-fpreserve-t0",  CROP43 + ",scale=480:360"),
            ("w800-h600-fpreserve-t0",  CROP43 + ",scale=800:600"),
            ("w1200-h630-fsmartcrop",   CROPOG + ",scale=1200:630"),
            # richiesto dal pannello media delle pagine servizio (project_media)
            ("h640-fpreserve-t0",       CROP43 + ",scale=-2:640"),
        ]:
            run(["ffmpeg", "-y", "-i", src, "-frames:v", "1", "-vf", vf,
                 "-q:v", "3", "-c:v", "mjpeg", "-f", "image2",
                 os.path.join(pd, name)])
        nseg = len(glob.glob(os.path.join(MUX, pid + "_*.ts")))
        size = sum(os.path.getsize(f) for f in glob.glob(os.path.join(MUX, pid + "_*.ts"))) // 1024
        print(f"[{slug:36}] {mp4:42} -> {pid[:18]}…  seg={nseg} {size}KB"
              + ("  (backup creato)" if b else ""))
    print("done.")

if __name__ == "__main__":
    main()
