#!/usr/bin/env python3
"""v5.1 = v5.0 features + continuous BatchScanActivity"""
from pathlib import Path
import os
import shutil
import subprocess
import sys

# First apply v5.0 if present
root = Path(__file__).resolve().parent
v50 = root / 'patch_v50.py'
if v50.exists():
    r = subprocess.run([sys.executable, str(v50)], check=False)
    print('patch_v50 exit', r.returncode)
else:
    print('WARNING: patch_v50.py missing')

proj = Path(os.environ['PROJ'])
src = proj / 'app/src/main/java/com/example/khanshgarzende'
res = proj / 'app/src/main/res'
manifest = proj / 'app/src/main/AndroidManifest.xml'

# Copy BatchScanActivity
batch_src = root.parent / 'app/src/main/java/com/example/khanshgarzende/BatchScanActivity.kt'
if not batch_src.exists():
    batch_src = Path('app/src/main/java/com/example/khanshgarzende/BatchScanActivity.kt')
if batch_src.exists():
    shutil.copy2(batch_src, src / 'BatchScanActivity.kt')
    print('BatchScanActivity.kt injected')
else:
    print('ERROR: BatchScanActivity.kt missing')
    sys.exit(1)

# Copy layout
lay_src = root.parent / 'app/src/main/res/layout/activity_batch_scan.xml'
if not lay_src.exists():
    lay_src = Path('app/src/main/res/layout/activity_batch_scan.xml')
lay_dir = res / 'layout'
lay_dir.mkdir(parents=True, exist_ok=True)
if lay_src.exists():
    shutil.copy2(lay_src, lay_dir / 'activity_batch_scan.xml')
    print('activity_batch_scan.xml injected')
else:
    print('ERROR: layout missing')
    sys.exit(1)

# Manifest
man = manifest.read_text(encoding='utf-8')
if 'BatchScanActivity' not in man:
    block = '''
        <activity android:name=".BatchScanActivity" android:theme="@style/AppTheme.NoBar"
            android:screenOrientation="portrait" android:exported="false" />
'''
    # insert after CameraActivity line if present
    if 'CameraActivity' in man:
        man = man.replace(
            'android:screenOrientation="portrait" android:exported="false" />',
            'android:screenOrientation="portrait" android:exported="false" />' + block,
            1,
        )
    else:
        man = man.replace('    </application>', block + '    </application>')
    manifest.write_text(man, encoding='utf-8')
    print('manifest: BatchScanActivity')

# Menu item
menu = res / 'menu/main_more.xml'
if menu.exists():
    m = menu.read_text(encoding='utf-8')
    if 'm_batch_scan' not in m:
        m = m.replace(
            '<item android:id="@+id/m_import"',
            '<item android:id="@+id/m_batch_scan" android:title="اسکن پیوسته (چندصفحه / کتاب)" />\n    <item android:id="@+id/m_import"',
        )
        menu.write_text(m, encoding='utf-8')
        print('menu: batch scan')

# MainActivity menu handler
main = src / 'MainActivity.kt'
if main.exists():
    mt = main.read_text(encoding='utf-8')
    if 'm_batch_scan' not in mt:
        mt = mt.replace(
            'R.id.m_import -> openPicker()',
            'R.id.m_batch_scan -> startActivity(Intent(this, BatchScanActivity::class.java))\n                R.id.m_import -> openPicker()',
        )
        main.write_text(mt, encoding='utf-8')
        print('MainActivity: batch scan menu')

# Version 5.1
bg = proj / 'app/build.gradle.kts'
if bg.exists():
    t = bg.read_text(encoding='utf-8')
    for old, new in [
        ('versionCode = 50', 'versionCode = 51'),
        ('versionCode = 40', 'versionCode = 51'),
        ('versionCode = 4', 'versionCode = 51'),
        ('versionName = "5.0"', 'versionName = "5.1"'),
        ('versionName = "4.0"', 'versionName = "5.1"'),
        ('versionName = "3.1"', 'versionName = "5.1"'),
    ]:
        t = t.replace(old, new)
    bg.write_text(t, encoding='utf-8')
    print('version -> 5.1')

print('ALL v5.1 PATCHES DONE')
