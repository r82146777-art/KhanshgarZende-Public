#!/usr/bin/env python3
"""v6.1: FIX — settings UI was hidden inside system_box (gone). Full rewrite of settings layout."""
from pathlib import Path
import os, re, subprocess, sys

root = Path(__file__).resolve().parent
r = subprocess.run([sys.executable, str(root / "patch_v60b.py")], check=False)
print("v60b", r.returncode)

proj = Path(os.environ["PROJ"])
src = proj / "app/src/main/java/com/example/khanshgarzende"
res = proj / "app/src/main/res"

layout_xml = r'''<?xml version="1.0" encoding="utf-8"?>
<ScrollView xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:layoutDirection="rtl"
    android:fillViewport="true">

<LinearLayout
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:orientation="vertical"
    android:padding="20dp">

    <TextView
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="نوع صوت"
        android:textStyle="bold"
        android:textSize="18sp"
        android:accessibilityHeading="true" />
    <RadioGroup
        android:id="@+id/voice_group"
        android:layout_width="match_parent"
        android:layout_height="wrap_content" />

    <LinearLayout
        android:id="@+id/system_box"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        android:visibility="gone">
        <TextView
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:textSize="15sp"
            android:text="موتور صدای نصب‌شده روی گوشی را انتخاب کنید." />
        <Spinner
            android:id="@+id/engine_spinner"
            android:layout_width="match_parent"
            android:layout_height="64dp"
            android:contentDescription="انتخاب موتور صدای گوشی" />
        <com.google.android.material.button.MaterialButton
            android:id="@+id/btn_tts_settings"
            style="@style/SecondaryButton"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="تنظیمات موتور صدای گوشی" />
    </LinearLayout>

    <LinearLayout
        android:id="@+id/azure_box"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        android:visibility="gone" />

    <TextView
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginTop="20dp"
        android:text="کلید API (تشخیص خودکار پلتفرم)"
        android:textStyle="bold"
        android:textSize="18sp"
        android:accessibilityHeading="true" />
    <TextView
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:textSize="14sp"
        android:text="فقط یک کلید وارد کنید. پلتفرم به‌صورت خودکار تشخیص داده می‌شود." />
    <EditText
        android:id="@+id/et_unified_api_key"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:hint="کلید API"
        android:inputType="textPassword"
        android:minHeight="52dp"
        android:textDirection="ltr" />
    <EditText
        android:id="@+id/et_custom_base_url"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:hint="آدرس پایه سفارشی (اختیاری)"
        android:minHeight="48dp"
        android:textDirection="ltr" />
    <com.google.android.material.button.MaterialButton
        android:id="@+id/btn_detect_test_key"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="تشخیص و تست کلید" />
    <TextView
        android:id="@+id/tv_api_status"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:padding="8dp"
        android:textSize="14sp" />

    <androidx.appcompat.widget.SwitchCompat
        android:id="@+id/sw_page_turn_sound"
        android:layout_width="match_parent"
        android:layout_height="64dp"
        android:text="صدای ورق خوردن صفحات"
        android:checked="true" />
    <androidx.appcompat.widget.SwitchCompat
        android:id="@+id/sw_offline_ai"
        android:layout_width="match_parent"
        android:layout_height="64dp"
        android:text="هوش مصنوعی آفلاین (OCR و تشخیص اشیا بدون اینترنت)"
        android:checked="true" />

    <TextView
        android:id="@+id/label_volume"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginTop="12dp"
        android:text="میزان صدا" />
    <SeekBar
        android:id="@+id/seek_volume"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:max="100" />
    <TextView
        android:id="@+id/label_rate"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="سرعت گفتار" />
    <SeekBar
        android:id="@+id/seek_rate"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:max="200" />
    <TextView
        android:id="@+id/label_pitch"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="زیر و بمی صدا" />
    <SeekBar
        android:id="@+id/seek_pitch"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:max="200" />

    <com.google.android.material.button.MaterialButton
        android:id="@+id/btn_test"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginTop="8dp"
        android:text="پخش نمونه صدا" />
    <com.google.android.material.button.MaterialButton
        android:id="@+id/btn_reset"
        style="@style/SecondaryButton"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="بازنشانی تنظیمات صدا" />

    <TextView
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginTop="16dp"
        android:text="فرمت فایل صوتی"
        android:textStyle="bold" />
    <RadioGroup
        android:id="@+id/format_group"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="horizontal">
        <RadioButton android:id="@+id/fmt_m4a" android:layout_width="wrap_content" android:layout_height="wrap_content" android:text="M4A" android:checked="true" />
        <RadioButton android:id="@+id/fmt_wav" android:layout_width="wrap_content" android:layout_height="wrap_content" android:text="WAV" />
    </RadioGroup>

    <androidx.appcompat.widget.SwitchCompat
        android:id="@+id/sw_paginate"
        android:layout_width="match_parent"
        android:layout_height="56dp"
        android:text="صفحه‌بندی خودکار متن" />
    <androidx.appcompat.widget.SwitchCompat
        android:id="@+id/sw_fallback"
        android:layout_width="match_parent"
        android:layout_height="56dp"
        android:text="پشتیبان آفلاین در صورت قطع اینترنت" />
    <androidx.appcompat.widget.SwitchCompat
        android:id="@+id/sw_auto"
        android:layout_width="match_parent"
        android:layout_height="56dp"
        android:text="تبدیل خودکار به صوت" />
    <androidx.appcompat.widget.SwitchCompat
        android:id="@+id/sw_scene"
        android:layout_width="match_parent"
        android:layout_height="56dp"
        android:text="توصیف صحنه در دوربین" />

    <TextView
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginTop="12dp"
        android:text="ارائه‌دهنده فعال"
        android:textStyle="bold" />
    <Spinner
        android:id="@+id/sp_online_provider"
        android:layout_width="match_parent"
        android:layout_height="48dp"
        android:minHeight="48dp" />

</LinearLayout>
</ScrollView>
'''
(res / "layout" / "activity_settings.xml").write_text(layout_xml, encoding="utf-8")
print("settings layout FULLY rewritten")

sm = src / "SpeechManager.kt"
st = sm.read_text(encoding="utf-8")
lines = []
for line in st.splitlines():
    low = line.lower()
    if (("dilara" in low or "farid" in low or "دلارا" in line or "فرید" in line)
        and ("list.add" in line or "Triple(" in line)):
        lines.append("            // v61 removed dilara/farid")
        continue
    lines.append(line)
st = "\n".join(lines)
st = st.replace(
    "دلارا و فرید: صدای طبیعی آنلاین مایکروسافت (نیاز به اینترنت و کلید Azure Speech)",
    "صداهای آفلاین Piper + صداهای API (کلید یکپارچه)",
)
if "fun pageTurnClick" not in st:
    idx = st.rfind("}")
    st = st[:idx] + '''
    fun pageTurnClick() {
        try {
            if (!prefs.pageTurnSound) return
            val tg = android.media.ToneGenerator(android.media.AudioManager.STREAM_MUSIC, 90)
            tg.startTone(android.media.ToneGenerator.TONE_PROP_BEEP, 45)
            android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                try { tg.startTone(android.media.ToneGenerator.TONE_PROP_ACK, 35) } catch (_: Throwable) {}
                android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                    try { tg.release() } catch (_: Throwable) {}
                }, 90)
            }, 55)
        } catch (_: Throwable) {}
    }
''' + st[idx:]
sm.write_text(st, encoding="utf-8")
print("SpeechManager cleaned")

sa = src / "SettingsActivity.kt"
sat = sa.read_text(encoding="utf-8")
inject = '''
        try {
            findViewById<androidx.appcompat.widget.SwitchCompat?>(R.id.sw_page_turn_sound)?.apply {
                isChecked = p.pageTurnSound
                setOnCheckedChangeListener { _, c -> p.pageTurnSound = c }
            }
            findViewById<androidx.appcompat.widget.SwitchCompat?>(R.id.sw_offline_ai)?.apply {
                isChecked = p.offlineAiEnabled
                setOnCheckedChangeListener { _, c -> p.offlineAiEnabled = c }
            }
            findViewById<android.widget.EditText?>(R.id.et_unified_api_key)?.setText(
                p.unifiedApiKey.ifBlank { p.azureKey }
            )
        } catch (_: Throwable) {}
'''
if "bindUnifiedApiV58()" in sat and "sw_page_turn_sound)?.apply" not in sat:
    sat = sat.replace("bindUnifiedApiV58()", inject + "\n        bindUnifiedApiV58()")
elif "updateBoxes()" in sat and "sw_offline_ai" not in sat:
    sat = sat.replace("updateBoxes()", inject + "\n        updateBoxes()")
sat = sat.replace(
    'if ((key == "dilara" || key == "farid") && !AzureTts.configured(p))',
    'if (false)',
)
sa.write_text(sat, encoding="utf-8")
print("Settings binds")

sd = src / "SceneDescriber.kt"
st = sd.read_text(encoding="utf-8")
st = st.replace("setConfidenceThreshold(0.55f)", "setConfidenceThreshold(0.40f)")
st = st.replace("setConfidenceThreshold(0.5f)", "setConfidenceThreshold(0.40f)")
sd.write_text(st, encoding="utf-8")

bg = proj / "app/build.gradle.kts"
bt = bg.read_text(encoding="utf-8")
bt = re.sub(r"versionCode\s*=\s*\d+", "versionCode = 61", bt)
bt = re.sub(r'versionName\s*=\s*"[^"]*"', 'versionName = "6.1"', bt)
bg.write_text(bt, encoding="utf-8")
print("ALL v6.1 DONE")
