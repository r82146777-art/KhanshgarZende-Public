#!/usr/bin/env python3
"""v5.8all: chain v57, overlay baked, inline fallbacks."""
from pathlib import Path
import os, shutil, subprocess, sys, re

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

# Prefs fallback fields
prefs = src / 'Prefs.kt'
pt = prefs.read_text(encoding='utf-8')
if 'unifiedApiKey' not in pt:
    extra = '''
    var unifiedApiKey: String
        get() = sp.getString("unified_api_key", "") ?: ""
        set(v) = sp.edit().putString("unified_api_key", v.trim()).apply()
    var detectedProvider: String
        get() = sp.getString("detected_provider", "") ?: ""
        set(v) = sp.edit().putString("detected_provider", v).apply()
    var apiIsPaid: Boolean
        get() = sp.getBoolean("api_is_paid", false)
        set(v) = sp.edit().putBoolean("api_is_paid", v).apply()
    var apiVoicesCsv: String
        get() = sp.getString("api_voices_csv", "") ?: ""
        set(v) = sp.edit().putString("api_voices_csv", v).apply()
    var pageTurnSound: Boolean
        get() = sp.getBoolean("page_turn_sound", true)
        set(v) = sp.edit().putBoolean("page_turn_sound", v).apply()
'''
    prefs.write_text(pt.rstrip()[:-1] + extra + '\n}\n', encoding='utf-8')
    print('Prefs fields added')

# VoicePacks: remove gyro if still present
vp = src / 'VoicePacks.kt'
vt = vp.read_text(encoding='utf-8')
if 'gyro' in vt:
    i = vt.find('val PACKS = listOf')
    j = vt.find('fun dir(', i)
    if i >= 0 and j > i:
        packs = '''val PACKS = listOf(
        Pack("amir", "امیر – مرد (آفلاین)", "vits-piper-fa_IR-amir-medium-int8", 21),
        Pack("reza", "رضا – مرد (آفلاین)", "vits-piper-fa_IR-reza_ibrahim-medium-int8", 21),
        Pack("ganji", "گنجی – مرد (آفلاین)", "vits-piper-fa_IR-ganji-medium-int8", 21),
        Pack("ganji_adabi", "گنجی ادبی – مرد (آفلاین)", "vits-piper-fa_IR-ganji_adabi-medium-int8", 20),
        Pack("mana", "مانا / مونا – زن (آفلاین ~۶۴مگ)", "mana-hf", 64),
        Pack("musa", "موسی – مرد آفلاین (معادل فرید)", "vits-piper-fa_IR-amir-medium-int8", 21),
        Pack("khadijah", "خدیجه – زن آفلاین (معادل دلارا)", "vits-piper-fa_IR-ganji-medium-int8", 21),
    )

    '''
        vp.write_text(vt[:i] + packs + vt[j:], encoding='utf-8')
        print('PACKS fixed')

# Camera objects-only
cam = src / 'CameraActivity.kt'
ct = cam.read_text(encoding='utf-8')
ct = ct.replace('اگر می‌خواهید متن را برایتان بخوانم، لطفاً دوربین را روی کتاب یا نوشته بگیرید.', 'دوربین را کمی بچرخانید تا اشیای بیشتری دیده شود.')
ct = ct.replace('speakThen("دوربین باز شد. دوربین را به سمت متن یا اطراف بگیرید.")', 'speakThen("دوربین باز شد. اشیای اطراف را توصیف می‌کنم.")')
if 'false && s.maybeText' not in ct:
    ct = ct.replace('s.maybeText ->', 'false && s.maybeText ->')
cam.write_text(ct, encoding='utf-8')
print('Camera')

# pageTurn in SpeechManager
sm = src / 'SpeechManager.kt'
st = sm.read_text(encoding='utf-8')
if 'pageTurnClick' not in st:
    idx = st.rfind('}')
    helper = '''
    fun pageTurnClick() {
        try {
            if (!prefs.pageTurnSound) return
            val tg = android.media.ToneGenerator(android.media.AudioManager.STREAM_MUSIC, 60)
            tg.startTone(android.media.ToneGenerator.TONE_PROP_ACK, 60)
            android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({ tg.release() }, 200)
        } catch (_: Throwable) {}
    }
'''
    sm.write_text(st[:idx] + helper + st[idx:], encoding='utf-8')
    print('pageTurn')

# layout API single box
layout = res_layout / 'activity_settings.xml'
lx = layout.read_text(encoding='utf-8')
if 'et_unified_api_key' not in lx:
    block = '''
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
        android:layout_marginTop="16dp" android:text="کلید API (تشخیص خودکار)" android:textStyle="bold" />
    <EditText android:id="@+id/et_unified_api_key" android:layout_width="match_parent" android:layout_height="wrap_content"
        android:hint="کلید API" android:inputType="textPassword" android:minHeight="52dp" android:textDirection="ltr" />
    <EditText android:id="@+id/et_custom_base_url" android:layout_width="match_parent" android:layout_height="wrap_content"
        android:hint="آدرس پایه سفارشی (اختیاری)" android:minHeight="48dp" android:textDirection="ltr" />
    <com.google.android.material.button.MaterialButton android:id="@+id/btn_detect_test_key"
        android:layout_width="match_parent" android:layout_height="wrap_content" android:text="تشخیص و تست کلید" />
    <TextView android:id="@+id/tv_api_status" android:layout_width="match_parent" android:layout_height="wrap_content" android:padding="8dp" />
    <androidx.appcompat.widget.SwitchCompat android:id="@+id/sw_page_turn_sound"
        android:layout_width="match_parent" android:layout_height="64dp" android:text="صدای ورق خوردن صفحات" />
'''
    if '</LinearLayout>' in lx:
        lx = lx.replace('</LinearLayout>', block + '\n</LinearLayout>', 1)
    else:
        lx += block
    layout.write_text(lx, encoding='utf-8')
    print('layout API')

# Settings bind detect button
sa = src / 'SettingsActivity.kt'
sat = sa.read_text(encoding='utf-8')
if 'bindUnifiedApiV58' not in sat:
    method = '''
    private fun bindUnifiedApiV58() {
        try {
            val p = prefs
            findViewById<android.widget.EditText>(R.id.et_unified_api_key)?.setText(
                p.unifiedApiKey.ifBlank { listOf(p.azureKey, p.openAiApiKey, p.openRouterApiKey).firstOrNull { it.isNotBlank() } ?: "" }
            )
            findViewById<androidx.appcompat.widget.SwitchCompat>(R.id.sw_page_turn_sound)?.apply {
                isChecked = p.pageTurnSound
                setOnCheckedChangeListener { _, c -> p.pageTurnSound = c }
            }
            findViewById<android.widget.Button>(R.id.btn_detect_test_key)?.setOnClickListener {
                val key = findViewById<android.widget.EditText>(R.id.et_unified_api_key)?.text?.toString()?.trim() ?: ""
                val base = findViewById<android.widget.EditText>(R.id.et_custom_base_url)?.text?.toString()?.trim() ?: ""
                if (key.isBlank()) { toast("کلید را وارد کنید"); return@setOnClickListener }
                p.unifiedApiKey = key
                if (base.isNotBlank()) p.customApiBaseUrl = base
                findViewById<android.widget.TextView>(R.id.tv_api_status)?.text = "در حال تست…"
                Thread {
                    val r = MultiTts.detectAndTest(key, base)
                    runOnUiThread {
                        if (r.ok) {
                            MultiTts.applyDetectToPrefs(p, r)
                            findViewById<android.widget.TextView>(R.id.tv_api_status)?.text = r.message
                            toast("کلید معتبر – ${r.label}")
                        } else {
                            findViewById<android.widget.TextView>(R.id.tv_api_status)?.text = r.message
                            toast("کلید کار نکرد")
                        }
                    }
                }.start()
            }
        } catch (e: Exception) { android.util.Log.e("Settings", "bindUnified", e) }
    }
'''
    if 'bindExtraSettingsV54()' in sat:
        sat = sat.replace('bindExtraSettingsV54()', 'bindExtraSettingsV54()\n        bindUnifiedApiV58()')
    elif 'btn_test' in sat:
        sat = sat.replace('findViewById<Button>(R.id.btn_test)', 'bindUnifiedApiV58()\n        findViewById<Button>(R.id.btn_test)', 1)
    idx = sat.rfind('}')
    sat = sat[:idx] + method + '\n' + sat[idx:]
    o, c = sat.count('{'), sat.count('}')
    if o > c:
        sat = sat.rstrip() + '\n' + ('}' * (o - c)) + '\n'
    sa.write_text(sat, encoding='utf-8')
    print('Settings bind')

bg = proj / 'app/build.gradle.kts'
bt = bg.read_text(encoding='utf-8')
bt = re.sub(r'versionCode\s*=\s*\d+', 'versionCode = 58', bt)
bt = re.sub(r'versionName\s*=\s*"[^"]*"', 'versionName = "5.8"', bt)
bg.write_text(bt, encoding='utf-8')
print('version 5.8')
print('ALL v5.8all DONE')
