#!/usr/bin/env python3
"""v5.8all: chain v57 then overlay baked sources."""
from pathlib import Path
import os, shutil, subprocess, sys

root = Path(__file__).resolve().parent
r = subprocess.run([sys.executable, str(root / 'patch_v57.py')], check=False)
print('v57 exit', r.returncode)

proj = Path(os.environ['PROJ'])
src = proj / 'app/src/main/java/com/example/khanshgarzende'
res_layout = proj / 'app/src/main/res/layout'
baked = root / 'baked'

mapping = {
    'MultiTts.kt': src / 'MultiTts.kt',
    'Prefs.kt': src / 'Prefs.kt',
    'SettingsActivity.kt': src / 'SettingsActivity.kt',
    'VoicePacks.kt': src / 'VoicePacks.kt',
    'CameraActivity.kt': src / 'CameraActivity.kt',
    'SpeechManager.kt': src / 'SpeechManager.kt',
    'activity_settings.xml': res_layout / 'activity_settings.xml',
}
for name, dest in mapping.items():
    srcf = baked / name
    if srcf.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(srcf, dest)
        print('overlay', name)
    else:
        print('missing baked', name)

bg = proj / 'app/build.gradle.kts'
bt = bg.read_text(encoding='utf-8')
for a,b in [('versionCode = 57','versionCode = 58'),('versionCode = 56','versionCode = 58'),
            ('versionName = "5.7"','versionName = "5.8"'),('versionName = "5.6"','versionName = "5.8"')]:
    bt = bt.replace(a,b)
bg.write_text(bt, encoding='utf-8')
print('version 5.8')
print('ALL v5.8all DONE')
