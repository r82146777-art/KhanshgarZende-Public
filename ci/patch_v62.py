#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
root = Path(__file__).resolve().parent
code = (root/"patch_v62_a.py").read_text() + (root/"patch_v62_b.py").read_text()
out = root/"_v62_run.py"
out.write_text(code)
raise SystemExit(subprocess.call([sys.executable, str(out)]))
