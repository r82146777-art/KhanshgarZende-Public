#!/usr/bin/env python3
"""v5.9 safe: page-turn, remove dilara/farid from list, single API key UI, no Settings break."""
from pathlib import Path
import os, re, subprocess, sys

root = Path(__file__).resolve().parent
r = subprocess.run([sys.executable, str(root / "patch_v58fix4.py")], check=False)
print("fix4", r.returncode)

proj = Path(os.environ["PROJ"])
src = proj / "app/src/main/java/com/example/khanshgarzende"
res = proj / "app/src/main/res"

sm = src / "SpeechManager.kt"
st = sm.read_text(encoding="utf-8")
out = []
for line in st.splitlines():
    low = line.lower()
    if (("dilara" in low or "farid" in low or "دلارا" in line or "فرید" in line)
        and ("list.add" in line or "Triple(" in line or "add(Triple" in line)):
        out.append("            // removed dilara/farid v59")
        continue
    out.append(line)
st = "\n".join(out)
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
print("SpeechManager OK")

tv = src / "TextViewerActivity.kt"
if tv.exists():
    tt = tv.read_text(encoding="utf-8")
    if "pageTurnClick" not in tt:
        for pat in ["currentPage++", "pageIndex++", "goNext()", "nextPage()", "setLastPage("]:
            if pat in tt:
                tt = tt.replace(pat, "try { app.speech.pageTurnClick() } catch (_: Throwable) {}\n        " + pat, 1)
                break
        for pat in ["currentPage--", "pageIndex--", "goPrev()", "prevPage()"]:
            if pat in tt:
                tt = tt.replace(pat, "try { app.speech.pageTurnClick() } catch (_: Throwable) {}\n        " + pat, 1)
                break
        tv.write_text(tt, encoding="utf-8")
        print("TextViewer wired")

prefs = src / "Prefs.kt"
pt = prefs.read_text(encoding="utf-8")
if "pageTurnSound" not in pt:
    idx = pt.rfind("}")
    prefs.write_text(pt[:idx] + '''
    var pageTurnSound: Boolean
        get() = sp.getBoolean("page_turn_sound", true)
        set(v) = sp.edit().putBoolean("page_turn_sound", v).apply()
''' + pt[idx:], encoding="utf-8")
else:
    prefs.write_text(pt.replace('getBoolean("page_turn_sound", false)', 'getBoolean("page_turn_sound", true)'), encoding="utf-8")

sa = src / "SettingsActivity.kt"
sat = sa.read_text(encoding="utf-8")

pat_azure = re.compile(
    r'[ \t]*val key = findViewById<EditText>\(R\.id\.azure_key\)\s*\n'
    r'[ \t]*val region = findViewById<EditText>\(R\.id\.azure_region\)\s*\n'
    r'[ \t]*key\.setText\(p\.azureKey\); region\.setText\(p\.azureRegion\)\s*\n'
    r'[ \t]*findViewById<Button>\(R\.id\.btn_azure_test\)\.setOnClickListener \{[\s\S]*?\n[ \t]*\}\s*\n'
    r'(?:[ \t]*\}\.start\(\)\s*\n)?'
    r'(?:[ \t]*\}\s*\n)?',
    re.M,
)
replacement = '''
        // v5.9: single unified API key (azure fields removed from layout)
        try {
            val uk = findViewById<EditText?>(R.id.et_unified_api_key)
            uk?.setText(p.unifiedApiKey.ifBlank { p.azureKey })
            findViewById<EditText?>(R.id.et_custom_base_url)?.setText(p.customBaseUrl)
            findViewById<androidx.appcompat.widget.SwitchCompat?>(R.id.sw_page_turn_sound)?.apply {
                isChecked = p.pageTurnSound
                setOnCheckedChangeListener { _, c -> p.pageTurnSound = c }
            }
        } catch (_: Throwable) {}

'''
if pat_azure.search(sat):
    sat = pat_azure.sub(replacement, sat, count=1)
    print("Settings azure block replaced (full)")
else:
    if "}.start()" in sat:
        sat = re.sub(r'[ \t]*\}\.start\(\)\s*\n[ \t]*\}\s*\n', '\n', sat, count=1)
        print("cleaned orphan }.start()")
    if "et_unified_api_key" not in sat or "sw_page_turn_sound" not in sat:
        inject = '''
        try {
            val uk = findViewById<EditText?>(R.id.et_unified_api_key)
            uk?.setText(p.unifiedApiKey.ifBlank { p.azureKey })
            findViewById<EditText?>(R.id.et_custom_base_url)?.setText(p.customBaseUrl)
            findViewById<androidx.appcompat.widget.SwitchCompat?>(R.id.sw_page_turn_sound)?.apply {
                isChecked = p.pageTurnSound
                setOnCheckedChangeListener { _, c -> p.pageTurnSound = c }
            }
        } catch (_: Throwable) {}
'''
        if "bindUnifiedApiV58()" in sat and "sw_page_turn_sound" not in sat:
            sat = sat.replace("bindUnifiedApiV58()", inject + "\n        bindUnifiedApiV58()")
            print("injected near bindUnified")

sat = sat.replace(
    'if ((key == "dilara" || key == "farid") && !AzureTts.configured(p))',
    'if (false && (key == "dilara" || key == "farid") && !AzureTts.configured(p))',
)
sat = re.sub(
    r'findViewById<View>\(R\.id\.azure_box\)\.visibility = if \(p\.voice == "dilara" \|\| p\.voice == "farid"\) View\.VISIBLE else View\.GONE',
    'findViewById<View?>(R.id.azure_box)?.visibility = View.GONE',
    sat,
)
sa.write_text(sat, encoding="utf-8")
t2 = sa.read_text(encoding="utf-8")
print("Settings braces", t2.count("{"), t2.count("}"), "lines", len(t2.splitlines()))
if t2.count("{") != t2.count("}"):
    lines = t2.splitlines()
    cleaned = []
    i = 0
    while i < len(lines):
        l = lines[i]
        if l.strip() == "}.start()":
            print("drop line", i+1, l)
            i += 1
            continue
        cleaned.append(l)
        i += 1
    t3 = "\n".join(cleaned)
    if t3.count("{") != t3.count("}"):
        bal = 0
        outl = []
        for l in t3.splitlines():
            bal += l.count("{") - l.count("}")
            if bal < 0 and l.strip() == "}":
                print("drop extra }")
                bal += 1
                continue
            outl.append(l)
        t3 = "\n".join(outl)
    sa.write_text(t3, encoding="utf-8")
    t2 = sa.read_text(encoding="utf-8")
    print("after cleanup braces", t2.count("{"), t2.count("}"))

layout = res / "layout" / "activity_settings.xml"
lx = layout.read_text(encoding="utf-8")
for rid in [
    "et_azure_key2", "et_azure_region2", "et_openai_key", "et_openrouter_key",
    "et_google_key", "et_deepseek_key", "et_grok_key", "et_custom_key", "et_custom_base",
    "azure_key", "azure_region",
]:
    lx = re.sub(rf'<EditText[^>]*android:id="@\+id/{rid}"[^/]*?/>', f'<!-- removed {rid} -->', lx, flags=re.S)
    lx = re.sub(rf'<EditText[^>]*android:id="@\+id/{rid}"[\s\S]*?</EditText>', f'<!-- removed {rid} -->', lx)
lx = re.sub(rf'<[^>]*android:id="@\+id/btn_azure_test"[^/]*?/>', '<!-- removed btn_azure_test -->', lx, flags=re.S)
lx = re.sub(
    rf'<[^>]*android:id="@\+id/btn_azure_test"[\s\S]*?</(?:Button|com\.google\.android\.material\.button\.MaterialButton)>',
    '<!-- removed btn_azure_test -->',
    lx,
)
if "et_unified_api_key" not in lx:
    block = '''
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
        android:layout_marginTop="16dp" android:text="کلید API (تشخیص خودکار پلتفرم)" android:textStyle="bold" />
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="فقط یک کلید وارد کنید؛ پلتفرم خودکار تشخیص داده می‌شود." android:textSize="13sp" />
    <EditText android:id="@+id/et_unified_api_key" android:layout_width="match_parent" android:layout_height="wrap_content"
        android:hint="کلید API" android:inputType="textPassword" android:minHeight="52dp" android:textDirection="ltr" />
    <EditText android:id="@+id/et_custom_base_url" android:layout_width="match_parent" android:layout_height="wrap_content"
        android:hint="آدرس پایه سفارشی (اختیاری)" android:minHeight="48dp" android:textDirection="ltr" />
    <com.google.android.material.button.MaterialButton android:id="@+id/btn_detect_test_key"
        android:layout_width="match_parent" android:layout_height="wrap_content" android:text="تشخیص و تست کلید" />
    <TextView android:id="@+id/tv_api_status" android:layout_width="match_parent" android:layout_height="wrap_content" android:padding="8dp" />
'''
    if "</LinearLayout>" in lx:
        lx = lx.replace("</LinearLayout>", block + "\n</LinearLayout>", 1)
    else:
        lx += block
if "sw_page_turn_sound" not in lx:
    sw = '''
    <androidx.appcompat.widget.SwitchCompat android:id="@+id/sw_page_turn_sound"
        android:layout_width="match_parent" android:layout_height="64dp"
        android:text="صدای ورق خوردن صفحات" android:checked="true" />
'''
    if "</LinearLayout>" in lx:
        lx = lx.replace("</LinearLayout>", sw + "\n</LinearLayout>", 1)
    else:
        lx += sw
lx = lx.replace("کلیدهای API (چندپلتفرم)", "کلید API")
layout.write_text(lx, encoding="utf-8")
print("layout OK")

vp = src / "VoicePacks.kt"
vt = vp.read_text(encoding="utf-8")
if "gyro" in vt or 'Pack("musa"' not in vt:
    i = vt.find("val PACKS = listOf")
    j = vt.find("fun dir(", i)
    if i >= 0 and j > i:
        packs = '''val PACKS = listOf(
        Pack("amir", "امیر – مرد (آفلاین)", "vits-piper-fa_IR-amir-medium-int8", 21),
        Pack("reza", "رضا – مرد (آفلاین)", "vits-piper-fa_IR-reza_ibrahim-medium-int8", 21),
        Pack("ganji", "گنجی – مرد (آفلاین)", "vits-piper-fa_IR-ganji-medium-int8", 21),
        Pack("ganji_adabi", "گنجی ادبی – مرد (آفلاین)", "vits-piper-fa_IR-ganji_adabi-medium-int8", 20),
        Pack("mana", "مانا / مونا – زن (آفلاین ~۶۴مگ)", "mana-hf", 64),
        Pack("musa", "موسی – مرد آفلاین (جایگزین فرید)", "vits-piper-fa_IR-amir-medium-int8", 21),
        Pack("khadijah", "خدیجه – زن آفلاین (جایگزین دلارا)", "vits-piper-fa_IR-ganji-medium-int8", 21),
    )

    '''
        vp.write_text(vt[:i] + packs + vt[j:], encoding="utf-8")
        print("PACKS OK")

bg = proj / "app/build.gradle.kts"
bt = bg.read_text(encoding="utf-8")
bt = re.sub(r"versionCode\s*=\s*\d+", "versionCode = 59", bt)
bt = re.sub(r'versionName\s*=\s*"[^"]*"', 'versionName = "5.9"', bt)
bg.write_text(bt, encoding="utf-8")
print("version 5.9")
print("ALL v5.9 SAFE DONE")
