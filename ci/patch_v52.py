#!/usr/bin/env python3
"""v5.2: voice guidance, photo capture, auto-photo settings, better scene, image share."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parent
for name in ('patch_v50.py', 'patch_v51.py'):
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
    print('ScanGuide injected')
else:
    print('WARNING no ScanGuide')

prefs = src / 'Prefs.kt'
if prefs.exists():
    t = prefs.read_text(encoding='utf-8')
    if 'autoPhoto' not in t:
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
        if idx > 0:
            prefs.write_text(t[:idx] + extra + '\n' + t[idx:], encoding='utf-8')
            print('Prefs: photo/guide')

lay = res / 'layout/activity_settings.xml'
if lay.exists():
    lx = lay.read_text(encoding='utf-8')
    if 'sw_auto_photo' not in lx:
        block = '''
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
        android:layout_marginTop="18dp" android:text="عکس و راهنما" android:textStyle="bold"
        android:textSize="18sp" android:textColor="@color/accent" />
    <com.google.android.material.switchmaterial.SwitchMaterial
        android:id="@+id/sw_voice_guide"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="راهنمای گویای موقعیت دوربین" android:checked="true" />
    <com.google.android.material.switchmaterial.SwitchMaterial
        android:id="@+id/sw_photo_button"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="گرفتن عکس فقط با دکمه" android:checked="true" />
    <com.google.android.material.switchmaterial.SwitchMaterial
        android:id="@+id/sw_auto_photo"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="عکس خودکار دوره‌ای (تشخیص محیط)" />
    <TextView android:id="@+id/lbl_auto_photo_sec"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="فاصلهٔ عکس خودکار: ۱۰ ثانیه" />
    <SeekBar android:id="@+id/seek_auto_photo"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:max="55" android:progress="5" />
'''
        if '</ScrollView>' in lx:
            lx = lx.replace('</ScrollView>', block + '</ScrollView>', 1)
        else:
            idx = lx.rfind('</LinearLayout>')
            lx = lx[:idx] + block + lx[idx:]
        lay.write_text(lx, encoding='utf-8')
        print('settings layout')

sa = src / 'SettingsActivity.kt'
if sa.exists():
    st = sa.read_text(encoding='utf-8')
    if 'sw_auto_photo' not in st and 'autoPhoto' not in st:
        inject = '''
        try {
            findViewById<com.google.android.material.switchmaterial.SwitchMaterial>(R.id.sw_voice_guide)?.apply {
                isChecked = p.voiceGuide
                setOnCheckedChangeListener { _, c -> p.voiceGuide = c }
            }
            findViewById<com.google.android.material.switchmaterial.SwitchMaterial>(R.id.sw_photo_button)?.apply {
                isChecked = p.photoByButtonOnly
                setOnCheckedChangeListener { _, c -> p.photoByButtonOnly = c }
            }
            findViewById<com.google.android.material.switchmaterial.SwitchMaterial>(R.id.sw_auto_photo)?.apply {
                isChecked = p.autoPhoto
                setOnCheckedChangeListener { _, c -> p.autoPhoto = c }
            }
            val lbl = findViewById<android.widget.TextView>(R.id.lbl_auto_photo_sec)
            val seek = findViewById<android.widget.SeekBar>(R.id.seek_auto_photo)
            if (seek != null) {
                seek.progress = (p.autoPhotoSeconds - 5).coerceIn(0, 55)
                lbl?.text = "فاصلهٔ عکس خودکار: ${p.autoPhotoSeconds} ثانیه"
                seek.setOnSeekBarChangeListener(object : android.widget.SeekBar.OnSeekBarChangeListener {
                    override fun onProgressChanged(s: android.widget.SeekBar?, progress: Int, fromUser: Boolean) {
                        val sec = progress + 5
                        p.autoPhotoSeconds = sec
                        lbl?.text = "فاصلهٔ عکس خودکار: $sec ثانیه"
                    }
                    override fun onStartTrackingTouch(s: android.widget.SeekBar?) {}
                    override fun onStopTrackingTouch(s: android.widget.SeekBar?) {}
                })
            }
        } catch (_: Throwable) {}
'''
        if 'buildVoices()' in st:
            st = st.replace('buildVoices()', inject + '\n        buildVoices()', 1)
        else:
            idx = st.find('private fun buildVoices')
            if idx < 0: idx = st.rfind('}')
            st = st[:idx] + inject + '\n' + st[idx:]
        sa.write_text(st, encoding='utf-8')
        print('SettingsActivity bound')

sd = src / 'SceneDescriber.kt'
if sd.exists():
    sdt = sd.read_text(encoding='utf-8')
    sdt2 = sdt.replace('setConfidenceThreshold(0.55f)', 'setConfidenceThreshold(0.45f)')
    sdt2 = sdt2.replace('if (names.size >= 6) break', 'if (names.size >= 10) break')
    if 'ScanGuide.forScene' not in sdt2:
        old = '''        val sentence = when {
            parts.isEmpty() -> "چیز مشخصی جلوی دوربین تشخیص داده نشد. گوشی را آرام به اطراف بچرخانید."
            else -> parts.joinToString(". ") + "."
        }'''
        new = '''        val sentence = try {
            ScanGuide.forScene(light, faces, names.toList(), maybeText)
        } catch (_: Throwable) {
            when {
                parts.isEmpty() -> "چیز مشخصی جلوی دوربین تشخیص داده نشد. گوشی را آرام به اطراف بچرخانید."
                else -> parts.joinToString(". ") + "."
            }
        }'''
        if old in sdt2:
            sdt2 = sdt2.replace(old, new)
    if sdt2 != sdt:
        sd.write_text(sdt2, encoding='utf-8')
        print('SceneDescriber improved')

cam = src / 'CameraActivity.kt'
if cam.exists():
    ct = cam.read_text(encoding='utf-8')
    if 'takeScenePhoto' not in ct:
        methods = '''
    private var lastPhotoAt = 0L
    private val photoHandler = android.os.Handler(android.os.Looper.getMainLooper())
    private val autoPhotoRunnable = object : Runnable {
        override fun run() {
            if (isFinishing) return
            if (app.prefs.autoPhoto && !app.prefs.photoByButtonOnly && mode != Mode.PAUSED && mode != Mode.BUSY) {
                takeScenePhoto(auto = true)
            }
            val sec = app.prefs.autoPhotoSeconds.coerceIn(5, 60)
            photoHandler.postDelayed(this, sec * 1000L)
        }
    }

    private fun startAutoPhotoLoop() {
        photoHandler.removeCallbacks(autoPhotoRunnable)
        if (app.prefs.autoPhoto && !app.prefs.photoByButtonOnly) {
            val sec = app.prefs.autoPhotoSeconds.coerceIn(5, 60)
            photoHandler.postDelayed(autoPhotoRunnable, sec * 1000L)
        }
    }

    private fun takeScenePhoto(auto: Boolean = false) {
        val now = android.os.SystemClock.elapsedRealtime()
        if (now - lastPhotoAt < 2000) return
        val cap = imageCapture ?: return
        lastPhotoAt = now
        setStatus(if (auto) "عکس خودکار…" else "در حال گرفتن عکس…")
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
        if 'speakThen("دوربین باز شد. دوربین را به سمت متن یا اطراف بگیرید.") { mode = Mode.SCANNING }' in ct:
            ct = ct.replace(
                'speakThen("دوربین باز شد. دوربین را به سمت متن یا اطراف بگیرید.") { mode = Mode.SCANNING }',
                'speakThen("دوربین باز شد. دوربین را به سمت متن یا اطراف بگیرید.") { mode = Mode.SCANNING; startAutoPhotoLoop() }',
                1,
            )
        if 'setOnLongClickListener' not in ct and 'preview.setOnClickListener' in ct:
            ct = ct.replace(
                'preview.setOnClickListener {',
                'preview.setOnLongClickListener { takeScenePhoto(false); true }\n        preview.setOnClickListener {',
                1,
            )
        if 'متن به‌خوبی خوانا نیست' in ct and 'ScanGuide' not in ct:
            ct = ct.replace(
                'val msg = "متن به‌خوبی خوانا نیست. گوشی را کمی دورتر یا نزدیک‌تر ببرید، نور را بیشتر کنید و ثابت نگه دارید."',
                'val bright = try { scene?.brightness(preview) ?: 80f } catch (_: Throwable) { 80f }\n'
                '            val msg = if (app.prefs.voiceGuide) ScanGuide.forTextScan(preview, r, bright) else '
                '"متن به‌خوبی خوانا نیست. گوشی را کمی دورتر یا نزدیک‌تر ببرید، نور را بیشتر کنید و ثابت نگه دارید."',
            )
        if 'photoHandler' in ct:
            ct = ct.replace(
                'override fun onDestroy() {\n        super.onDestroy()',
                'override fun onDestroy() {\n        photoHandler.removeCallbacks(autoPhotoRunnable)\n        super.onDestroy()',
                1,
            )
        cam.write_text(ct, encoding='utf-8')
        print('CameraActivity photo+guide')

bs = src / 'BatchScanActivity.kt'
if bs.exists():
    bt = bs.read_text(encoding='utf-8')
    if 'در حال خواندن… گوشی را صاف' not in bt:
        bt = bt.replace(
            'setStatus("در حال خواندن صفحه… ثابت نگه دارید")',
            'setStatus("در حال خواندن… گوشی را صاف و ثابت بالای صفحه نگه دارید")',
        )
        bt = bt.replace(
            'doneFail("متن خوانا نیست. نور و فاصله را تنظیم کنید")',
            'doneFail("متن خوانا نیست. گوشی را حدود سی سانتی‌متر بالای صفحه صاف بگیرید و نور را بهتر کنید")',
        )
        bt = bt.replace(
            'setStatus("صفحهٔ ${pages.size} ذخیره شد. صفحهٔ بعد یا «پایان و ذخیره».")',
            'setStatus("صفحهٔ ${pages.size} ذخیره شد. صفحه را ورق بزنید و دوباره گرفتن صفحه را بزنید.")',
        )
        bs.write_text(bt, encoding='utf-8')
        print('BatchScan guidance')

main = src / 'MainActivity.kt'
if main.exists():
    mt = main.read_text(encoding='utf-8')
    if 'image/*' not in mt:
        mt = mt.replace(
            'pickFile.launch(arrayOf(\n            "application/pdf", "text/*", "application/msword",',
            'pickFile.launch(arrayOf(\n            "application/pdf", "text/*", "image/*", "application/msword",',
        )
        main.write_text(mt, encoding='utf-8')
        print('MainActivity image picker')

bg = proj / 'app/build.gradle.kts'
if bg.exists():
    t = bg.read_text(encoding='utf-8')
    for old, new in [
        ('versionCode = 51', 'versionCode = 52'),
        ('versionCode = 50', 'versionCode = 52'),
        ('versionName = "5.1"', 'versionName = "5.2"'),
        ('versionName = "5.0"', 'versionName = "5.2"'),
    ]:
        t = t.replace(old, new)
    bg.write_text(t, encoding='utf-8')
    print('version -> 5.2')

print('ALL v5.2 PATCHES DONE')
