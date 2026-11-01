#!/usr/bin/env python3
import base64, pathlib, subprocess, sys
root = pathlib.Path(__file__).resolve().parent
parts = []
for i in range(13):
    ns = {}
    exec((root / f"patch_v62_c{i:02d}.py").read_text(), ns)
    parts.append(ns[f"C{i:02d}"])
raw = base64.b64decode("".join(parts))
out = root / "_v62_run.py"
out.write_bytes(raw)
raise SystemExit(subprocess.call([sys.executable, str(out)]))
