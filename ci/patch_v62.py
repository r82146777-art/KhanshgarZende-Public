#!/usr/bin/env python3
"""v6.2 wrapper — downloads full patch from Drive then runs it."""
from pathlib import Path
import os, re, subprocess, sys, urllib.request, http.cookiejar

root = Path(__file__).resolve().parent

def download_drive(file_id: str, dest: Path):
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    resp = opener.open(url, timeout=120)
    data = resp.read()
    if b'confirm' in data[:2000] or data[:1] != b'#':
        text = data.decode('utf-8', 'ignore')
        m = re.search(r'name="confirm"\s+value="([^"]+)"', text)
        confirm = m.group(1) if m else 't'
        m2 = re.search(r'name="uuid"\s+value="([^"]+)"', text)
        uuid = m2.group(1) if m2 else ''
        url2 = f'https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm={confirm}&uuid={uuid}'
        data = opener.open(url2, timeout=120).read()
    dest.write_bytes(data)
    print('downloaded', dest, len(data))

# Prefer local full patch next to this file if present and large enough
local_full = root / 'patch_v62_full.py'
if not local_full.exists() or local_full.stat().st_size < 5000:
    try:
        download_drive('1OmwP4Bnb2N-FeArtYZE4WOdAdNF69PDF', local_full)
    except Exception as e:
        print('drive download failed', e)
        # fallback: run embedded minimal path via v61b only
        r = subprocess.run([sys.executable, str(root / 'patch_v61b.py')], check=False)
        sys.exit(r.returncode)

r = subprocess.run([sys.executable, str(local_full)], check=False)
sys.exit(r.returncode)
