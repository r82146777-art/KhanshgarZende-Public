#!/usr/bin/env python3
"""v5.4c: fix ocr.recognize(bitmap) -> recognize(bitmap, false)."""
from pathlib import Path
import os
import re

proj = Path(os.environ['PROJ'])
src = proj / 'app/src/main/java/com/example/khanshgarzende'

for name in ('CameraActivity.kt', 'BatchScanActivity.kt'):
    f = src / name
    if not f.exists():
        continue
    t = f.read_text(encoding='utf-8')
    t2 = re.sub(r'ocr\.recognize\(([^,\)]+)\)', r'ocr.recognize(\1, false)', t)
    # avoid double false, false
    t2 = t2.replace(', false, false)', ', false)')
    if t2 != t:
        f.write_text(t2, encoding='utf-8')
        print(name, 'recognize arity fixed')
    else:
        print(name, 'no change')

# Ensure settings XML still valid
lay = proj / 'app/src/main/res/layout/activity_settings.xml'
if lay.exists():
    try:
        import xml.etree.ElementTree as ET
        ET.parse(lay)
        print('settings XML still OK')
    except Exception as e:
        print('settings XML broken, rebuild', e)
        # run minimal rebuild like 54b
        lines = lay.read_text(encoding='utf-8').splitlines()
        out = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if any(s in line for s in ('sw_voice_guide', 'btn_accessibility', 'عکس و راهنما', 'دسترس‌پذیری')):
                break
            out.append(line)
            if 'sw_scene' in line:
                if '/>' not in line:
                    i += 1
                    while i < len(lines):
                        out.append(lines[i])
                        if '/>' in lines[i]:
                            break
                        i += 1
                break
            i += 1
        while out and out[-1].strip() in ('</LinearLayout>', '</ScrollView>', ''):
            out.pop()
        block = '''
    <com.google.android.material.button.MaterialButton
        android:id="@+id/btn_accessibility"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="باز کردن دسترس‌پذیری گوشی (خواندن با صدای بلند)" />
    <androidx.appcompat.widget.SwitchCompat android:id="@+id/sw_voice_guide"
        android:layout_width="match_parent" android:layout_height="64dp"
        android:text="راهنمای گویای موقعیت دوربین و اسکنر" />
    <androidx.appcompat.widget.SwitchCompat android:id="@+id/sw_photo_button"
        android:layout_width="match_parent" android:layout_height="64dp"
        android:text="عکس فقط با دکمه (نه خودکار)" />
    <androidx.appcompat.widget.SwitchCompat android:id="@+id/sw_auto_photo"
        android:layout_width="match_parent" android:layout_height="64dp"
        android:text="عکس خودکار دوره‌ای در تشخیص محیط" />
    <TextView android:id="@+id/lbl_auto_photo_sec"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="فاصلهٔ عکس خودکار: ۱۰ ثانیه" />
    <SeekBar android:id="@+id/seek_auto_photo"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:max="55" android:progress="5" />
</LinearLayout>
</ScrollView>
'''
        lay.write_text('\n'.join(out) + '\n' + block, encoding='utf-8')
        print('rebuilt settings')

print('v5.4c done')
