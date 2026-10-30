#!/usr/bin/env python3
"""v5.3: fix Settings crash, accessibility entry, scanner voice guide, camera photo button."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parent
for name in ('patch_v50.py', 'patch_v51.py', 'patch_v52.py'):
    p = root / name
    if p.exists():
        r = subprocess.run([sys.executable, str(p)], check=False)
        print(name, 'exit', r.returncode)

proj = Path(os.environ['PROJ'])
src = proj / 'app/src/main/java/com/example/khanshgarzende'
res = proj / 'app/src/main/res'

guide_src = root.parent / 'app/src/main/java/com/example/khanshgarzende/ScanGuide.kt'
if not guide_src.exists():
    guide_src = Path('app/src/main/java/com/example/khanshgarzende/ScanGuide.kt')
if guide_src.exists():
    shutil.copy2(guide_src, src / 'ScanGuide.kt')
    print('ScanGuide ok')

prefs = src / 'Prefs.kt'
if prefs.exists():
    t = prefs.read_text(encoding='utf-8')
    if 'voiceGuide' not in t:
        extra = '''
    var autoPhoto: Boolean
        get() = sp.getBoolean("auto_photo", false)
        set(v) = sp.edit().putBoolean("auto_photo", v).apply()
    var autoPhotoSeconds: Int
        get() = sp.getInt("auto_photo_seconds", 10).coerceIn(5, 60)
        set(v) = sp.edit().putInt("auto_photo_seconds", v.coerceIn(5, 60)).apply()
    var photoByButtonOnly: Boolean
        get() = sp.getBoolean("photo_by_button", true)
        set(v) = sp.edit().putBoolean("photo_by_button", v).apply()
    var voiceGuide: Boolean
        get() = sp.getBoolean("voice_guide", true)
        set(v) = sp.edit().putBoolean("voice_guide", v).apply()
'''
        idx = t.rfind('}')
        prefs.write_text(t[:idx] + extra + '\n' + t[idx:], encoding='utf-8')
        print('Prefs fixed')

lay = res / 'layout/activity_settings.xml'
if lay.exists():
    lx = lay.read_text(encoding='utf-8')
    lx = lx.replace(
        'com.google.android.material.switchmaterial.SwitchMaterial',
        'androidx.appcompat.widget.SwitchCompat',
    )
    if 'btn_accessibility' not in lx:
        block = '''
    <TextView style="@style/Label" android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:layout_marginTop="16dp" android:text="دسترس‌پذیری و راهنما" android:textStyle="bold"
        android:textSize="18sp" android:accessibilityHeading="true" />
    <com.google.android.material.button.MaterialButton
        android:id="@+id/btn_accessibility"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="باز کردن دسترس‌پذیری گوشی (خواندن با صدای بلند)"
        android:contentDescription="باز کردن تنظیمات دسترس‌پذیری سیستم" />
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
        android:textSize="14sp"
        android:text="پس از باز شدن صفحه، خواندن با صدای بلند – خوانشگر زنده را پیدا و روشن کنید." />
    <androidx.appcompat.widget.SwitchCompat android:id="@+id/sw_voice_guide"
        android:layout_width="match_parent" android:layout_height="64dp"
        android:textSize="17sp" android:text="راهنمای گویای موقعیت دوربین و اسکنر" />
    <androidx.appcompat.widget.SwitchCompat android:id="@+id/sw_photo_button"
        android:layout_width="match_parent" android:layout_height="64dp"
        android:textSize="17sp" android:text="عکس فقط با دکمه (نه خودکار)" />
    <androidx.appcompat.widget.SwitchCompat android:id="@+id/sw_auto_photo"
        android:layout_width="match_parent" android:layout_height="64dp"
        android:textSize="17sp" android:text="عکس خودکار دوره‌ای در تشخیص محیط" />
    <TextView android:id="@+id/lbl_auto_photo_sec"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="فاصلهٔ عکس خودکار: ۱۰ ثانیه" android:textSize="16sp" />
    <SeekBar android:id="@+id/seek_auto_photo"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:max="55" android:progress="5" />
'''
        if 'sw_voice_guide' in lx:
            # already has switches from v52; just add accessibility button at top of that section
            if 'btn_accessibility' not in lx:
                lx = lx.replace(
                    'android:id="@+id/sw_voice_guide"',
                    'android:id="@+id/btn_accessibility" android:text="باز کردن دسترس‌پذیری گوشی" />\n    <androidx.appcompat.widget.SwitchCompat android:id="@+id/sw_voice_guide"',
                    1,
                )
                # fix broken tag if SwitchCompat line got mangled - rewrite section simply
        else:
            if '</LinearLayout>\n</ScrollView>' in lx:
                lx = lx.replace('</LinearLayout>\n</ScrollView>', block + '</LinearLayout>\n</ScrollView>', 1)
            elif '</ScrollView>' in lx:
                lx = lx.replace('</ScrollView>', block + '</ScrollView>', 1)
            else:
                idx = lx.rfind('</LinearLayout>')
                lx = lx[:idx] + block + lx[idx:]
        lay.write_text(lx, encoding='utf-8')
        print('settings layout')

# Clean settings layout properly if mangled
lay = res / 'layout/activity_settings.xml'
if lay.exists():
    lx = lay.read_text(encoding='utf-8')
    # If btn_accessibility was incorrectly applied as SwitchCompat attributes, rebuild tail
    if 'btn_accessibility' in lx and 'MaterialButton' not in lx[lx.find('btn_accessibility'):lx.find('btn_accessibility')+200]:
        # strip from دسترس or عکس و راهنما to before </LinearLayout></ScrollView>
        import re
        lx2 = re.sub(
            r'(<TextView[^>]*عکس و راهنما.*?</SeekBar>)',
            '',
            lx,
            count=1,
            flags=re.S,
        )
        block = '''
    <TextView style="@style/Label" android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:layout_marginTop="16dp" android:text="دسترس‌پذیری و راهنما" android:textStyle="bold"
        android:textSize="18sp" android:accessibilityHeading="true" />
    <com.google.android.material.button.MaterialButton
        android:id="@+id/btn_accessibility"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="باز کردن دسترس‌پذیری گوشی (خواندن با صدای بلند)" />
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
        android:textSize="14sp"
        android:text="پس از باز شدن صفحه، خواندن با صدای بلند – خوانشگر زنده را پیدا و روشن کنید." />
    <androidx.appcompat.widget.SwitchCompat android:id="@+id/sw_voice_guide"
        android:layout_width="match_parent" android:layout_height="64dp"
        android:textSize="17sp" android:text="راهنمای گویای موقعیت دوربین و اسکنر" />
    <androidx.appcompat.widget.SwitchCompat android:id="@+id/sw_photo_button"
        android:layout_width="match_parent" android:layout_height="64dp"
        android:textSize="17sp" android:text="عکس فقط با دکمه (نه خودکار)" />
    <androidx.appcompat.widget.SwitchCompat android:id="@+id/sw_auto_photo"
        android:layout_width="match_parent" android:layout_height="64dp"
        android:textSize="17sp" android:text="عکس خودکار دوره‌ای در تشخیص محیط" />
    <TextView android:id="@+id/lbl_auto_photo_sec"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="فاصلهٔ عکس خودکار: ۱۰ ثانیه" android:textSize="16sp" />
    <SeekBar android:id="@+id/seek_auto_photo"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:max="55" android:progress="5" />
'''
        if 'btn_accessibility' not in lx2 or 'MaterialButton' not in lx2:
            # remove any leftover broken sw_voice section and append clean block
            for mid in ('sw_voice_guide', 'sw_photo_button', 'sw_auto_photo', 'seek_auto_photo', 'lbl_auto_photo_sec', 'btn_accessibility'):
                pass
            if '</LinearLayout>\n</ScrollView>' in lx2:
                # remove lines containing those ids
                lines = lx2.splitlines()
                out = []
                skip = False
                for line in lines:
                    if any(x in line for x in ('sw_voice_guide', 'sw_photo_button', 'sw_auto_photo', 'seek_auto_photo', 'lbl_auto_photo_sec', 'btn_accessibility', 'عکس و راهنما', 'دسترس‌پذیری و راهنما')):
                        continue
                    out.append(line)
                lx2 = '\n'.join(out)
                lx2 = lx2.replace('</LinearLayout>\n</ScrollView>', block + '</LinearLayout>\n</ScrollView>', 1)
            lay.write_text(lx2, encoding='utf-8')
            print('settings layout cleaned')
        else:
            lay.write_text(lx, encoding='utf-8')

sa = src / 'SettingsActivity.kt'
if sa.exists():
    st = sa.read_text(encoding='utf-8')
    st = st.replace(
        'findViewById<com.google.android.material.switchmaterial.SwitchMaterial>',
        'findViewById<SwitchCompat>',
    )
    if 'bindExtraSettingsV53' not in st:
        method = '''
    private fun bindExtraSettingsV53() {
        try {
            findViewById<Button>(R.id.btn_accessibility)?.setOnClickListener {
                try {
                    startActivity(android.content.Intent(android.provider.Settings.ACTION_ACCESSIBILITY_SETTINGS))
                } catch (e: Exception) {
                    toast("باز کردن دسترس‌پذیری ممکن نشد")
                }
            }
            findViewById<SwitchCompat>(R.id.sw_voice_guide)?.let { sw ->
                sw.isChecked = try { p.voiceGuide } catch (_: Throwable) { true }
                sw.setOnCheckedChangeListener { _, c -> try { p.voiceGuide = c } catch (_: Throwable) {} }
            }
            findViewById<SwitchCompat>(R.id.sw_photo_button)?.let { sw ->
                sw.isChecked = try { p.photoByButtonOnly } catch (_: Throwable) { true }
                sw.setOnCheckedChangeListener { _, c -> try { p.photoByButtonOnly = c } catch (_: Throwable) {} }
            }
            findViewById<SwitchCompat>(R.id.sw_auto_photo)?.let { sw ->
                sw.isChecked = try { p.autoPhoto } catch (_: Throwable) { false }
                sw.setOnCheckedChangeListener { _, c -> try { p.autoPhoto = c } catch (_: Throwable) {} }
            }
            val lbl = findViewById<TextView>(R.id.lbl_auto_photo_sec)
            val seek = findViewById<SeekBar>(R.id.seek_auto_photo)
            if (seek != null) {
                val sec0 = try { p.autoPhotoSeconds } catch (_: Throwable) { 10 }
                seek.progress = (sec0 - 5).coerceIn(0, 55)
                lbl?.text = "فاصلهٔ عکس خودکار: " + sec0 + " ثانیه"
                seek.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                    override fun onProgressChanged(s: SeekBar?, progress: Int, fromUser: Boolean) {
                        val sec = progress + 5
                        try { p.autoPhotoSeconds = sec } catch (_: Throwable) {}
                        lbl?.text = "فاصلهٔ عکس خودکار: " + sec + " ثانیه"
                    }
                    override fun onStartTrackingTouch(s: SeekBar?) {}
                    override fun onStopTrackingTouch(s: SeekBar?) {}
                })
            }
        } catch (e: Throwable) {
            android.util.Log.e("Settings", "bindExtraSettingsV53", e)
        }
    }

'''
        if 'updateBoxes()' in st:
            st = st.replace('updateBoxes()', 'bindExtraSettingsV53()\n        updateBoxes()', 1)
        idx = st.rfind('}')
        st = st[:idx] + method + '\n' + st[idx:]
    sa.write_text(st, encoding='utf-8')
    print('SettingsActivity safe bind')

cam_lay = res / 'layout/activity_camera.xml'
if cam_lay.exists():
    cl = cam_lay.read_text(encoding='utf-8')
    if 'btn_photo' not in cl:
        needle = 'android:id="@+id/btn_save"'
        if needle in cl:
            cl = cl.replace(
                needle,
                'android:id="@+id/btn_photo" style="@style/SecondaryButton" android:text="گرفتن عکس" android:contentDescription="گرفتن عکس" />\n            <com.google.android.material.button.MaterialButton android:id="@+id/btn_save"',
                1,
            )
            # Fix possible attribute duplication on btn_save line - the original btn_save had style on same element
            cam_lay.write_text(cl, encoding='utf-8')
            print('camera photo button')

cam = src / 'CameraActivity.kt'
if cam.exists():
    ct = cam.read_text(encoding='utf-8')
    if 'R.id.btn_photo' not in ct:
        if 'btnSave.setOnClickListener' in ct:
            ct = ct.replace(
                'btnSave.setOnClickListener { saveText() }',
                'btnSave.setOnClickListener { saveText() }\n        try { findViewById<Button>(R.id.btn_photo)?.setOnClickListener { takeScenePhoto(false) } } catch (_: Throwable) {}',
                1,
            )
    if 'fun takeScenePhoto' not in ct:
        methods = '''
    private var lastPhotoAt = 0L
    private val photoHandler = android.os.Handler(android.os.Looper.getMainLooper())
    private val autoPhotoRunnable = object : Runnable {
        override fun run() {
            if (isFinishing) return
            try {
                if (app.prefs.autoPhoto && !app.prefs.photoByButtonOnly && mode != Mode.PAUSED && mode != Mode.BUSY) takeScenePhoto(true)
            } catch (_: Throwable) {}
            try { photoHandler.postDelayed(this, app.prefs.autoPhotoSeconds.coerceIn(5, 60) * 1000L) } catch (_: Throwable) {}
        }
    }
    private fun startAutoPhotoLoop() {
        photoHandler.removeCallbacks(autoPhotoRunnable)
        try {
            if (app.prefs.autoPhoto && !app.prefs.photoByButtonOnly)
                photoHandler.postDelayed(autoPhotoRunnable, app.prefs.autoPhotoSeconds.coerceIn(5, 60) * 1000L)
        } catch (_: Throwable) {}
    }
    private fun takeScenePhoto(auto: Boolean = false) {
        val now = android.os.SystemClock.elapsedRealtime()
        if (now - lastPhotoAt < 2000) return
        val cap = imageCapture ?: run { toast("دوربین آماده نیست"); return }
        lastPhotoAt = now
        setStatus(if (auto) "عکس خودکار…" else "در حال گرفتن عکس…")
        try { app.speech.speak(if (auto) "عکس خودکار" else "در حال گرفتن عکس") } catch (_: Throwable) {}
        val dir = java.io.File(filesDir, "photos").apply { mkdirs() }
        val f = java.io.File(dir, "photo_${System.currentTimeMillis()}.jpg")
        val opts = ImageCapture.OutputFileOptions.Builder(f).build()
        cap.takePicture(opts, worker, object : ImageCapture.OnImageSavedCallback {
            override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                runOnUiThread {
                    setStatus("عکس ذخیره شد")
                    try { app.speech.speak("عکس ذخیره شد") } catch (_: Throwable) {}
                    toast("عکس ذخیره شد")
                }
            }
            override fun onError(exception: ImageCaptureException) {
                runOnUiThread { setStatus("خطا در گرفتن عکس") }
            }
        })
    }
'''
        if 'override fun onDestroy' in ct:
            ct = ct.replace('override fun onDestroy()', methods + '\n    override fun onDestroy()')
    if 'startAutoPhotoLoop' in ct:
        ct = ct.replace(
            'speakThen("دوربین باز شد. دوربین را به سمت متن یا اطراف بگیرید.") { mode = Mode.SCANNING }',
            'speakThen("دوربین باز شد. برای عکس دکمه گرفتن عکس را بزنید.") { mode = Mode.SCANNING; startAutoPhotoLoop() }',
            1,
        )
    cam.write_text(ct, encoding='utf-8')
    print('CameraActivity ok')

bs = src / 'BatchScanActivity.kt'
if bs.exists():
    bt = bs.read_text(encoding='utf-8')
    if 'اسکن پیوسته آماده است' not in bt:
        bt = bt.replace(
            'setStatus("آماده. صفحه را بگیرید و «گرفتن صفحه» را بزنید.")',
            'setStatus("آماده. صفحه را بگیرید و گرفتن صفحه را بزنید.")\n'
            '                try { if (app.prefs.voiceGuide) app.speech.speak("اسکن پیوسته آماده است. گوشی را بالای صفحه صاف بگیرید و دکمه گرفتن صفحه را بزنید.") } catch (_: Throwable) {}',
        )
        bt = bt.replace(
            'setStatus("آماده. صفحه را بگیرید و گرفتن صفحه را بزنید.")',
            'setStatus("آماده. صفحه را بگیرید و گرفتن صفحه را بزنید.")\n'
            '                try { if (app.prefs.voiceGuide) app.speech.speak("اسکن پیوسته آماده است. گوشی را بالای صفحه صاف بگیرید و دکمه گرفتن صفحه را بزنید.") } catch (_: Throwable) {}',
        )
    if 'private fun doneFail' in bt and 'app.speech.speak(msg)' not in bt:
        bt = bt.replace(
            'private fun doneFail(msg: String) = runOnUiThread {\n        busy = false; btnCapture.isEnabled = true; setStatus(msg); beep(false)\n    }',
            'private fun doneFail(msg: String) = runOnUiThread {\n'
            '        busy = false; btnCapture.isEnabled = true; setStatus(msg); beep(false)\n'
            '        try { if (app.prefs.voiceGuide) app.speech.speak(msg) } catch (_: Throwable) {}\n'
            '    }',
        )
    if 'ثابت نگه دارید")' in bt and 'speak("ثابت' not in bt:
        bt = bt.replace(
            'setStatus("در حال خواندن… گوشی را صاف و ثابت بالای صفحه نگه دارید")',
            'setStatus("در حال خواندن… گوشی را صاف و ثابت بالای صفحه نگه دارید")\n'
            '        try { if (app.prefs.voiceGuide) app.speech.speak("ثابت نگه دارید") } catch (_: Throwable) {}',
        )
    bs.write_text(bt, encoding='utf-8')
    print('BatchScan voice')

bg = proj / 'app/build.gradle.kts'
if bg.exists():
    t = bg.read_text(encoding='utf-8')
    for old, new in [
        ('versionCode = 52', 'versionCode = 53'),
        ('versionCode = 51', 'versionCode = 53'),
        ('versionName = "5.2"', 'versionName = "5.3"'),
        ('versionName = "5.1"', 'versionName = "5.3"'),
    ]:
        t = t.replace(old, new)
    bg.write_text(t, encoding='utf-8')
    print('version -> 5.3')

print('ALL v5.3 PATCHES DONE')
