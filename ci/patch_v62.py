#!/usr/bin/env python3
import base64, pathlib, subprocess, sys
root = pathlib.Path(__file__).resolve().parent
ns = {}
exec((root/"patch_v62_p1.py").read_text(), ns)
exec((root/"patch_v62_p2.py").read_text(), ns)
raw = base64.b64decode(ns["PART1"] + ns["PART2"])
out = root / "_v62_run.py"
out.write_bytes(raw)
raise SystemExit(subprocess.call([sys.executable, str(out)]))
