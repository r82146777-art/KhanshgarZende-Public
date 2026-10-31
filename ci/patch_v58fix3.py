#!/usr/bin/env python3
from pathlib import Path
import os, re, subprocess, sys

root = Path(__file__).resolve().parent
r = subprocess.run([sys.executable, str(root / 'patch_v58fix2.py')], check=False)
print('fix2', r.returncode)

proj = Path(os.environ['PROJ'])
sm = proj / 'app/src/main/java/com/example/khanshgarzende/SpeechManager.kt'
st = sm.read_text(encoding='utf-8')
# Fix nullable Pair assignment - use elvis empty
st = st.replace(
    'MultiTts.synthPcm(prefs, text)?.let { it to 22050 }',
    '(MultiTts.synthPcm(prefs, text) ?: (ShortArray(0) to 22050))',
)
st = st.replace(
    'MultiTts.synthPcm(p, text)?.let { it to 22050 }',
    '(MultiTts.synthPcm(p, text) ?: (ShortArray(0) to 22050))',
)
# also handle direct assignment patterns
st = re.sub(
    r'MultiTts\.synthPcm\(([^)]+)\)\?\.let \{ it to 22050 \}',
    r'(MultiTts.synthPcm(\1) ?: (ShortArray(0) to 22050))',
    st,
)
sm.write_text(st, encoding='utf-8')
print('SpeechManager nullable fixed')
print('fix3 DONE')
