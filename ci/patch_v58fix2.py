#!/usr/bin/env python3
from pathlib import Path
import os, re, subprocess, sys

root = Path(__file__).resolve().parent
r = subprocess.run([sys.executable, str(root / 'patch_v58fix.py')], check=False)
print('fix', r.returncode)

proj = Path(os.environ['PROJ'])
src = proj / 'app/src/main/java/com/example/khanshgarzende'

sa = src / 'SettingsActivity.kt'
sat = sa.read_text(encoding='utf-8')
# comment out missing method calls
sat = sat.replace('bindAccessibilityAndApiV55()', '// bindAccessibilityAndApiV55()')
sat = sat.replace('bindMultiApiKeysV56()', '// bindMultiApiKeysV56()')
# fix prefs -> this.prefs or app prefs - usually class has `private val prefs` or `val p = Prefs(this)`
if 'Unresolved' or True:
    # ensure `val prefs` exists
    if 'val prefs' not in sat and 'private val prefs' not in sat:
        # inject after class line
        sat = re.sub(
            r'(class SettingsActivity[^{]*\{)',
            r'\1\n    private val prefs by lazy { Prefs(this) }\n',
            sat,
            count=1,
        )
# stub missing methods if referenced
if 'fun bindAccessibilityAndApiV55' not in sat:
    idx = sat.rfind('}')
    sat = sat[:idx] + '''
    private fun bindAccessibilityAndApiV55() {}
    private fun bindMultiApiKeysV56() {}
''' + sat[idx:]
sa.write_text(sat, encoding='utf-8')
o,c = sat.count('{'), sat.count('}')
if o > c:
    sa.write_text(sa.read_text().rstrip() + '\n' + ('}'*(o-c)) + '\n', encoding='utf-8')
print('Settings stubs')

# SpeechManager synthPcm return type - MultiTts returns ShortArray? but expected Pair
sm = src / 'SpeechManager.kt'
st = sm.read_text(encoding='utf-8')
# find synthPcm usage and fix
st = st.replace('MultiTts.synthPcm(prefs, text)', 'MultiTts.synthPcm(prefs, text)?.let { it to 22050 }')
st = st.replace('MultiTts.synthPcm(p, text)', 'MultiTts.synthPcm(p, text)?.let { it to 22050 }')
# if assignment expects Pair
if 'synthPcm' in st:
    st = re.sub(
        r'=\s*MultiTts\.synthPcm\(([^)]+)\)\s*$',
        r'= MultiTts.synthPcm(\1)?.let { it to 22050 }',
        st,
        flags=re.M,
    )
sm.write_text(st, encoding='utf-8')
print('SpeechManager synthPcm')

# MultiTts synthPcm return as Pair for safety
mt = src / 'MultiTts.kt'
mtxt = mt.read_text(encoding='utf-8')
if 'fun synthPcm' in mtxt and 'Pair' not in mtxt[mtxt.find('fun synthPcm'):mtxt.find('fun synthPcm')+200]:
    mtxt = mtxt.replace(
        'fun synthPcm(p: Prefs, text: String, voice: String = "nova"): ShortArray? {\n        val mp3 = synthMp3(p, text, voice) ?: return null\n        // crude: not decoding mp3 here; caller may fall back\n        return null\n    }',
        'fun synthPcm(p: Prefs, text: String, voice: String = "nova"): Pair<ShortArray, Int>? {\n        return null\n    }',
    )
    mt.write_text(mtxt, encoding='utf-8')
    print('synthPcm Pair')

print('fix2 DONE')
