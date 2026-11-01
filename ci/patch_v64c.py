#!/usr/bin/env python3
from pathlib import Path
import os, re, subprocess, sys
root = Path(__file__).resolve().parent
print('v64b', subprocess.run([sys.executable, str(root/'patch_v64b.py')], check=False).returncode)
proj = Path(os.environ['PROJ'])
sa = proj/'app/src/main/java/com/example/khanshgarzende/SettingsActivity.kt'
t = sa.read_text(encoding='utf-8')
# Close any empty bindMultiApiKeysV56 opening brace before next function
t = re.sub(
    r'private fun bindMultiApiKeysV56\(\)\s*\{\s*\n(\s*)private fun showAppPicker',
    r'private fun bindMultiApiKeysV56() {}\n\n\1private fun showAppPicker',
    t,
)
# If still unbalanced, append one closing brace before EOF class end is wrong - fix bal
while t.count('{') > t.count('}'):
    # insert before final class closer if exists
    if t.rstrip().endswith('}'):
        # missing close somewhere; add at end before last }
        t = t.rstrip()[:-1] + '}\n}\n'
        break
    else:
        t = t + '}\n'
        break
# Prefer exact balance: if one extra }, remove last orphan - skip
sa.write_text(t, encoding='utf-8')
print('Settings braces', t.count('{'), t.count('}'))
# version already 6.4
print('v64c DONE')
