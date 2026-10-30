#!/usr/bin/env python3
"""v5.4b: force-clean activity_settings.xml after prior broken injections."""
from pathlib import Path
import os

proj = Path(os.environ['PROJ'])
lay = proj / 'app/src/main/res/layout/activity_settings.xml'
if not lay.exists():
    raise SystemExit('no settings layout')

lx = lay.read_text(encoding='utf-8')
lines = lx.splitlines()
out = []
i = 0
while i < len(lines):
    line = lines[i]
    # stop collecting once we hit previously injected junk
    if any(s in line for s in (
        'sw_voice_guide', 'sw_photo_button', 'sw_auto_photo', 'seek_auto_photo',
        'lbl_auto_photo_sec', 'btn_accessibility', 'عکس و راهنما', 'دسترس‌پذیری و راهنما',
    )):
        break
    out.append(line)
    if 'sw_scene' in line:
        # include rest of this element if multi-line
        if '/>' not in line and '</androidx.appcompat.widget.SwitchCompat>' not in line:
            i += 1
            while i < len(lines):
                out.append(lines[i])
                if '/>' in lines[i] or '</androidx.appcompat.widget.SwitchCompat>' in lines[i]:
                    break
                i += 1
        break
    i += 1

# Drop trailing close tags from out; we will re-add them
while out and out[-1].strip() in ('</LinearLayout>', '</ScrollView>', ''):
    out.pop()

block = '''
    <TextView style="@style/Label" android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:layout_marginTop="16dp" android:text="دسترس‌پذیری و راهنما" android:textStyle="bold"
        android:textSize="18sp" android:accessibilityHeading="true" />
    <com.google.android.material.button.MaterialButton
        android:id="@+id/btn_accessibility"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="باز کردن دسترس‌پذیری گوشی (خواندن با صدای بلند)"
        android:contentDescription="باز کردن تنظیمات دسترس‌پذیری سیستم" />
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
        android:textSize="14sp"
        android:text="پس از باز شدن صفحه، خواندن با صدای بلند – خوانشگر زنده را پیدا و روشن کنید." />
    <androidx.appcompat.widget.SwitchCompat
        android:id="@+id/sw_voice_guide"
        android:layout_width="match_parent"
        android:layout_height="64dp"
        android:textSize="17sp"
        android:text="راهنمای گویای موقعیت دوربین و اسکنر" />
    <androidx.appcompat.widget.SwitchCompat
        android:id="@+id/sw_photo_button"
        android:layout_width="match_parent"
        android:layout_height="64dp"
        android:textSize="17sp"
        android:text="عکس فقط با دکمه (نه خودکار)" />
    <androidx.appcompat.widget.SwitchCompat
        android:id="@+id/sw_auto_photo"
        android:layout_width="match_parent"
        android:layout_height="64dp"
        android:textSize="17sp"
        android:text="عکس خودکار دوره‌ای در تشخیص محیط" />
    <TextView
        android:id="@+id/lbl_auto_photo_sec"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="فاصلهٔ عکس خودکار: ۱۰ ثانیه"
        android:textSize="16sp" />
    <SeekBar
        android:id="@+id/seek_auto_photo"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:max="55"
        android:progress="5" />
</LinearLayout>
</ScrollView>
'''

lay.write_text('\n'.join(out) + '\n' + block, encoding='utf-8')
print('settings XML rebuilt cleanly, lines', len(out))

# Also hard-fix camera btn_photo dimensions if still broken
cam_lay = proj / 'app/src/main/res/layout/activity_camera.xml'
if cam_lay.exists():
    cl = cam_lay.read_text(encoding='utf-8')
    lines = []
    for line in cl.splitlines():
        if 'btn_photo' in line and 'layout_width' not in line:
            lines.append(
                '            <com.google.android.material.button.MaterialButton android:id="@+id/btn_photo" style="@style/SecondaryButton"\n'
                '                android:layout_width="0dp" android:layout_weight="1" android:layout_height="wrap_content"\n'
                '                android:text="گرفتن عکس"\n'
                '                android:contentDescription="گرفتن عکس از صحنهٔ فعلی" />'
            )
        else:
            lines.append(line)
    cam_lay.write_text('\n'.join(lines), encoding='utf-8')
    print('camera btn_photo checked')

print('v5.4b done')
