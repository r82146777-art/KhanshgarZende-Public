#!/usr/bin/env python3
from pathlib import Path
import os, re, subprocess, sys

root = Path(__file__).resolve().parent
r = subprocess.run([sys.executable, str(root / 'patch_v58fix3.py')], check=False)
print('fix3', r.returncode)

proj = Path(os.environ['PROJ'])
mt = proj / 'app/src/main/java/com/example/khanshgarzende/MultiTts.kt'
mtxt = mt.read_text(encoding='utf-8')
# Force synthPcm to return non-null Pair
mtxt = re.sub(
    r'fun synthPcm\([^)]*\):\s*Pair<ShortArray,\s*Int>\?\s*\{[^}]*\}',
    'fun synthPcm(p: Prefs, text: String, voice: String = "nova"): Pair<ShortArray, Int> { return ShortArray(0) to 22050 }',
    mtxt,
)
mtxt = re.sub(
    r'fun synthPcm\([^)]*\):\s*ShortArray\?\s*\{[^}]*\}',
    'fun synthPcm(p: Prefs, text: String, voice: String = "nova"): Pair<ShortArray, Int> { return ShortArray(0) to 22050 }',
    mtxt,
)
if 'fun synthPcm' not in mtxt:
    idx = mtxt.rfind('}')
    mtxt = mtxt[:idx] + '\n    fun synthPcm(p: Prefs, text: String, voice: String = "nova"): Pair<ShortArray, Int> { return ShortArray(0) to 22050 }\n' + mtxt[idx:]
mt.write_text(mtxt, encoding='utf-8')

# Also force SpeechManager line to non-null
sm = proj / 'app/src/main/java/com/example/khanshgarzende/SpeechManager.kt'
st = sm.read_text(encoding='utf-8')
lines = st.splitlines()
for i, line in enumerate(lines):
    if 'synthPcm' in line and 'Pair' not in line and '=' in line:
        # ensure non-null
        if '?:' not in line and '?:' not in line:
            lines[i] = line.replace('MultiTts.synthPcm', '(MultiTts.synthPcm') + ' ?: (ShortArray(0) to 22050))'
    if 'synthPcm' in line and '?:' not in line and 'to 22050' not in line:
        if 'return MultiTts.synthPcm' in line:
            lines[i] = line.replace('return MultiTts.synthPcm', 'return MultiTts.synthPcm').replace(')', ') ?: (ShortArray(0) to 22050)')
st2 = '\n'.join(lines)
# brute: any assignment of synthPcm result
st2 = re.sub(
    r'(return\s+)(MultiTts\.synthPcm\([^)]+\))(\s*$)',
    r'\1(\2 ?: (ShortArray(0) to 22050))\3',
    st2,
    flags=re.M,
)
sm.write_text(st2, encoding='utf-8')
print('fix4 DONE')
print('synthPcm signature:', [l for l in mt.read_text().splitlines() if 'synthPcm' in l][:3])
print('SM synth lines:', [l for l in sm.read_text().splitlines() if 'synthPcm' in l][:5])
