#!/usr/bin/env python3
"""v6.1b: layout rewrite + missing settings IDs for bindExtraSettingsV54."""
from pathlib import Path
import os, re, subprocess, sys

root = Path(__file__).resolve().parent
r = subprocess.run([sys.executable, str(root / "patch_v61.py")], check=False)
print("v61", r.returncode)

proj = Path(os.environ["PROJ"])
res = proj / "app/src/main/res"
layout = res / "layout" / "activity_settings.xml"
lx = layout.read_text(encoding="utf-8")

extra = '''
    <com.google.android.material.button.MaterialButton
        android:id="@+id/btn_accessibility"
        style="@style/SecondaryButton"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginTop="12dp"
        android:text="باز کردن تنظیمات دسترس‌پذیری گوشی" />
    <androidx.appcompat.widget.SwitchCompat
        android:id="@+id/sw_voice_guide"
        android:layout_width="match_parent"
        android:layout_height="56dp"
        android:text="راهنمای گویا در اسکنر و دوربین" />
    <androidx.appcompat.widget.SwitchCompat
        android:id="@+id/sw_photo_button"
        android:layout_width="match_parent"
        android:layout_height="56dp"
        android:text="دکمه گرفتن عکس در دوربین" />
    <androidx.appcompat.widget.SwitchCompat
        android:id="@+id/sw_auto_photo"
        android:layout_width="match_parent"
        android:layout_height="56dp"
        android:text="عکس خودکار دوربین" />
    <androidx.appcompat.widget.SwitchCompat
        android:id="@+id/sw_read_all_apps"
        android:layout_width="match_parent"
        android:layout_height="56dp"
        android:text="خواندن با صدای بلند در همه برنامه‌ها" />
'''

for rid in ["btn_accessibility", "sw_voice_guide", "sw_photo_button", "sw_auto_photo", "sw_read_all_apps"]:
    if rid not in lx:
        if "</LinearLayout>\n</ScrollView>" in lx:
            lx = lx.replace("</LinearLayout>\n</ScrollView>", extra + "\n</LinearLayout>\n</ScrollView>", 1)
        elif "</LinearLayout>" in lx:
            lx = lx.replace("</LinearLayout>", extra + "\n</LinearLayout>", 1)
        else:
            lx += extra
        break

layout.write_text(lx, encoding="utf-8")
print("extra controls added")

bg = proj / "app/build.gradle.kts"
bt = bg.read_text(encoding="utf-8")
bt = re.sub(r"versionCode\s*=\s*\d+", "versionCode = 61", bt)
bt = re.sub(r'versionName\s*=\s*"[^"]*"', 'versionName = "6.1"', bt)
bg.write_text(bt, encoding="utf-8")
print("v6.1b DONE")
