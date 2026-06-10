#!/usr/bin/env python3
"""Download missing local assets for the mirror from shader.se.

Usage:
    python3 fetch_assets.py /textures/foo.webp /textures/icons/bar.svg ...

- Each arg is a root-relative path (as the page requests it from 127.0.0.1).
- Fetches https://www.shader.se/<path> and saves to mirror_root/<path> if 200.
- For a /videos/prebaked/<dir>/*.manifest.json it also pulls every sheet file
  listed in the manifest (same directory).
- Skips files already present. Prints a one-line status per asset.
"""
import os, sys, json, urllib.request, urllib.error

BASE = "https://www.shader.se"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mirror_root")
UA = {"User-Agent": "Mozilla/5.0 (mirror-tool)"}

def get(path):
    url = f"{BASE}/{path.lstrip('/')}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def save(path, data):
    dest = os.path.join(ROOT, path.lstrip("/"))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(data)
    return dest

def fetch_one(path):
    dest = os.path.join(ROOT, path.lstrip("/"))
    if os.path.isfile(dest):
        return "skip (exists)"
    try:
        data = get(path)
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"
    except Exception as e:
        return f"ERR {e}"
    save(path, data)
    note = f"ok ({len(data)} B)"
    # prebaked manifest -> also grab its sheets
    if path.endswith(".manifest.json"):
        try:
            man = json.loads(data)
            d = os.path.dirname(path)
            n = 0
            for s in man.get("sheets", []):
                sp = f"{d}/{s['file']}"
                if not os.path.isfile(os.path.join(ROOT, sp.lstrip("/"))):
                    save(sp, get(sp)); n += 1
            note += f" + {n} sheets"
        except Exception as e:
            note += f" (sheet err: {e})"
    return note

def main(paths):
    for p in paths:
        print(f"{fetch_one(p):<28} {p}")

if __name__ == "__main__":
    main(sys.argv[1:])
