#!/usr/bin/env python3
"""v5.4: fix Settings/Camera crash (broken XML), paste text in library, gallery pick."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parent
for name in ('patch_v50.py', 'patch_v51.py', 'patch_v52.py', 'patch_v53.py'):
    p = root / name
    if p.exists():
        r = subprocess.run([sys.executable, str(p)], check=False)
        print(name, 'exit', r.returncode)

proj = Path(os.environ['PROJ'])
src = proj / 'app/src/main/java/com/example/khanshgarzende'
res = proj / 'app/src/main/res'

for rel in (
    'app/src/main/java/com/example/khanshgarzende/ReadAloudService.kt',
    'app/src/main/java/com/example/khanshgarzende/BatchScanActivity.kt',
    'app/src/main/java/com/example/khanshgarzende/ScanGuide.kt',
    'app/src/main/res/layout/activity_batch_scan.xml',
):
    cand = root.parent / rel
    if not cand.exists():
        cand = Path(rel)
    if cand.exists():
        dest = proj / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cand, dest)
        print('copied', rel)

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

lay = res / 'layout/activity_settings.xml'
if lay.exists():
    lx = lay.read_text(encoding='utf-8')
    skip_ids = (
        'sw_voice_guide', 'sw_photo_button', 'sw_auto_photo', 'seek_auto_photo',
        'lbl_auto_photo_sec', 'btn_accessibility', 'عکس و راهنما', 'دسترس‌پذیری و راهنما',
        'باز کردن دسترس', 'راهنمای گویای', 'عکس فقط با دکمه', 'عکس خودکار دوره‌ای',
        'فاصلهٔ عکس خودکار',
    )
    cleaned = []
    for line in lx.splitlines():
        if any(s in line for s in skip_ids):
            continue
        cleaned.append(line)
    lx = '\n'.join(cleaned)
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
'''
    idx = lx.rfind('</LinearLayout>')
    if idx > 0:
        lx = lx[:idx] + block + '\n' + lx[idx:]
    lay.write_text(lx, encoding='utf-8')
    print('settings layout FIXED')

sa = src / 'SettingsActivity.kt'
if sa.exists():
    st = sa.read_text(encoding='utf-8')
    st = st.replace(
        'findViewById<com.google.android.material.switchmaterial.SwitchMaterial>',
        'findViewById<SwitchCompat>',
    )
    st = re.sub(
        r'\n\s*try \{\s*\n\s*findViewById<SwitchCompat>\(R\.id\.sw_voice_guide\)\?\.apply \{[\s\S]*?\n\s*\} catch \(_: Throwable\) \{\}\s*\n\s*buildVoices\(\)',
        '\n        buildVoices()',
        st,
        count=1,
    )
    if 'bindExtraSettingsV54' not in st:
        method = '''
    private fun bindExtraSettingsV54() {
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
            android.util.Log.e("Settings", "bindExtraSettingsV54", e)
        }
    }

'''
        if 'updateBoxes()' in st:
            st = st.replace('updateBoxes()', 'bindExtraSettingsV54()\n        updateBoxes()', 1)
        st = st.replace('bindExtraSettingsV53()\n        ', '')
        idx = st.rfind('}')
        st = st[:idx] + method + '\n' + st[idx:]
    else:
        st = st.replace('bindExtraSettingsV53()', 'bindExtraSettingsV54()')
        st = st.replace('fun bindExtraSettingsV53', 'fun bindExtraSettingsV54')
    sa.write_text(st, encoding='utf-8')
    print('SettingsActivity fixed')

cam_lay = res / 'layout/activity_camera.xml'
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
    cl = '\n'.join(lines)
    if 'btn_gallery' not in cl:
        cl = cl.replace(
            'android:id="@+id/btn_back"',
            'android:id="@+id/btn_gallery" style="@style/SecondaryButton"\n'
            '                android:layout_width="0dp" android:layout_weight="1" android:layout_height="wrap_content"\n'
            '                android:layout_marginStart="8dp"\n'
            '                android:text="گالری"\n'
            '                android:contentDescription="انتخاب عکس از گالری" />\n'
            '            <com.google.android.material.button.MaterialButton android:id="@+id/btn_back"',
            1,
        )
    cam_lay.write_text(cl, encoding='utf-8')
    print('camera layout FIXED')

cam = src / 'CameraActivity.kt'
if cam.exists():
    ct = cam.read_text(encoding='utf-8')
    if 'pickGalleryImage' not in ct:
        gallery_code = '''
    private val pickGalleryImage = registerForActivityResult(androidx.activity.result.contract.ActivityResultContracts.GetContent()) { uri ->
        if (uri == null) return@registerForActivityResult
        worker.execute {
            try {
                val bmp = android.provider.MediaStore.Images.Media.getBitmap(contentResolver, uri)
                val r = ocr.recognize(bmp)
                bmp.recycle()
                val cleaned = try { PersianText.cleanOcrText(r.text) } catch (_: Throwable) { r.text }
                runOnUiThread {
                    if (PersianText.letterCount(cleaned) < 3) {
                        setStatus("در این عکس متن خوانایی پیدا نشد")
                        try { if (app.prefs.voiceGuide) app.speech.speak("در این عکس متن خوانایی پیدا نشد") } catch (_: Throwable) {}
                    } else {
                        lastText = cleaned
                        showText(cleaned)
                        setStatus("متن از گالری خوانده شد")
                        findViewById<Button>(R.id.btn_save)?.isEnabled = true
                        try { app.speech.speak(cleaned.take(400)) } catch (_: Throwable) {}
                    }
                }
            } catch (e: Throwable) {
                runOnUiThread { setStatus("خطا در خواندن عکس گالری"); toast("خطا در خواندن عکس") }
            }
        }
    }
'''
        ct = ct.replace('override fun onCreate', gallery_code + '\n    override fun onCreate')
        insert = '''
        try { findViewById<Button>(R.id.btn_photo)?.setOnClickListener { takeScenePhoto(false) } } catch (_: Throwable) {}
        try { findViewById<Button>(R.id.btn_gallery)?.setOnClickListener { pickGalleryImage.launch("image/*") } } catch (_: Throwable) {}
'''
        if 'btnSave.setOnClickListener' in ct:
            ct = ct.replace('btnSave.setOnClickListener { saveText() }', 'btnSave.setOnClickListener { saveText() }' + insert, 1)
        if 'fun takeScenePhoto' not in ct:
            methods = '''
    private var lastPhotoAt = 0L
    private val photoHandler = android.os.Handler(android.os.Looper.getMainLooper())
    private val autoPhotoRunnable = object : Runnable {
        override fun run() {
            if (isFinishing) return
            try {
                if (app.prefs.autoPhoto && !app.prefs.photoByButtonOnly && mode != Mode.PAUSED && mode != Mode.BUSY)
                    takeScenePhoto(true)
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
                ct = ct.replace('override fun onDestroy()', methods + '\n    override fun onDestroy()', 1)
        if 'photoHandler.removeCallbacks' not in ct and 'override fun onDestroy' in ct:
            ct = ct.replace(
                'override fun onDestroy() {\n        super.onDestroy()',
                'override fun onDestroy() {\n        try { photoHandler.removeCallbacks(autoPhotoRunnable) } catch (_: Throwable) {}\n        super.onDestroy()',
                1,
            )
        ct = ct.replace('ScanGuide.forTextScan(preview, r, bright)', 'ScanGuide.forTextScan(null, r, 80f)')
        ct = ct.replace('PersianText.cleanOcr(', 'PersianText.cleanOcrText(')
        cam.write_text(ct, encoding='utf-8')
        print('CameraActivity gallery+photo')

bs_lay = res / 'layout/activity_batch_scan.xml'
if bs_lay.exists():
    bl = bs_lay.read_text(encoding='utf-8')
    if 'btn_batch_gallery' not in bl and 'btn_batch_capture' in bl:
        bl = bl.replace(
            'android:id="@+id/btn_batch_capture"',
            'android:id="@+id/btn_batch_gallery" style="@style/SecondaryButton"\n'
            '                android:layout_width="0dp" android:layout_weight="1" android:layout_height="wrap_content"\n'
            '                android:text="گالری" />\n'
            '            <com.google.android.material.button.MaterialButton android:id="@+id/btn_batch_capture"',
            1,
        )
        bs_lay.write_text(bl, encoding='utf-8')

bs = src / 'BatchScanActivity.kt'
if bs.exists():
    bt = bs.read_text(encoding='utf-8')
    bt = bt.replace('PersianText.cleanOcr(', 'PersianText.cleanOcrText(')
    if 'pickGalleryImage' not in bt:
        gal = '''
    private val pickGalleryImage = registerForActivityResult(androidx.activity.result.contract.ActivityResultContracts.GetContent()) { uri ->
        if (uri == null) return@registerForActivityResult
        if (busy) return@registerForActivityResult
        busy = true
        setStatus("در حال خواندن از گالری…")
        worker.execute {
            try {
                val bmp = android.provider.MediaStore.Images.Media.getBitmap(contentResolver, uri)
                val r = ocr.recognize(bmp)
                bmp.recycle()
                var text = try { PersianText.cleanOcrText(r.text) } catch (_: Throwable) { r.text }
                text = text.trim()
                if (PersianText.letterCount(text) < 3) {
                    runOnUiThread {
                        busy = false
                        setStatus("متن خوانا نبود")
                        try { if (app.prefs.voiceGuide) app.speech.speak("متن خوانا نبود") } catch (_: Throwable) {}
                    }
                    return@execute
                }
                pages.add(text)
                runOnUiThread {
                    busy = false
                    counter.text = "صفحات: " + pages.size
                    textView.text = text.take(500)
                    setStatus("صفحه از گالری اضافه شد. تعداد: " + pages.size)
                    try { if (app.prefs.voiceGuide) app.speech.speak("صفحه اضافه شد") } catch (_: Throwable) {}
                }
            } catch (e: Throwable) {
                runOnUiThread { busy = false; setStatus("خطا در گالری") }
            }
        }
    }
'''
        bt = bt.replace('override fun onCreate', gal + '\n    override fun onCreate')
        if 'btnCapture.setOnClickListener' in bt:
            bt = bt.replace(
                'btnCapture.setOnClickListener { capturePage() }',
                'btnCapture.setOnClickListener { capturePage() }\n'
                '        try { findViewById<Button>(R.id.btn_batch_gallery)?.setOnClickListener { pickGalleryImage.launch("image/*") } } catch (_: Throwable) {}',
            )
    bs.write_text(bt, encoding='utf-8')
    print('BatchScan gallery')

lib_lay = res / 'layout/activity_library.xml'
if lib_lay.exists():
    ll = lib_lay.read_text(encoding='utf-8')
    if 'paste_box' not in ll:
        paste = '''
    <LinearLayout android:id="@+id/paste_box" android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="vertical" android:padding="10dp" android:background="@color/surface">
        <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
            android:text="جایگذاری متن (کوتاه یا طولانی)" android:textStyle="bold" android:textSize="16sp" />
        <EditText android:id="@+id/paste_input"
            android:layout_width="match_parent" android:layout_height="120dp"
            android:gravity="top|right" android:inputType="textMultiLine|textLongMessage"
            android:hint="متن را اینجا بچسبانید…" android:minLines="4" android:maxLines="12"
            android:padding="8dp" />
        <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
            android:orientation="horizontal" android:layout_marginTop="6dp">
            <com.google.android.material.button.MaterialButton android:id="@+id/btn_paste_save"
                android:layout_width="0dp" android:layout_weight="1" android:layout_height="wrap_content"
                android:text="ذخیره متن" />
            <com.google.android.material.button.MaterialButton android:id="@+id/btn_paste_audio" style="@style/SecondaryButton"
                android:layout_width="0dp" android:layout_weight="1" android:layout_height="wrap_content"
                android:layout_marginStart="8dp" android:text="تبدیل به صوت" />
        </LinearLayout>
    </LinearLayout>
'''
        if '</LinearLayout>\n    <FrameLayout' in ll:
            ll = ll.replace('</LinearLayout>\n    <FrameLayout', '</LinearLayout>\n' + paste + '    <FrameLayout', 1)
            lib_lay.write_text(ll, encoding='utf-8')
            print('library layout paste')

lib = src / 'LibraryActivity.kt'
if lib.exists():
    lt = lib.read_text(encoding='utf-8')
    if 'btn_paste_save' not in lt:
        if 'android.widget.EditText' not in lt:
            lt = lt.replace('import android.widget.Button', 'import android.widget.Button\nimport android.widget.EditText')
        bind = '''
        try {
            val pasteInput = findViewById<EditText>(R.id.paste_input)
            findViewById<Button>(R.id.btn_paste_save)?.setOnClickListener {
                val text = pasteInput?.text?.toString()?.trim().orEmpty()
                if (text.length < 2) { toast("متن خالی است"); return@setOnClickListener }
                Thread {
                    val id = app.db.addText("متن جایگذاری‌شده", text)
                    runOnUiThread {
                        toast("ذخیره شد")
                        pasteInput?.setText("")
                        type = "text"
                        tabs.getTabAt(0)?.select()
                        reload()
                        try { app.speech.speak("متن ذخیره شد") } catch (_: Throwable) {}
                    }
                }.start()
            }
            findViewById<Button>(R.id.btn_paste_audio)?.setOnClickListener {
                val text = pasteInput?.text?.toString()?.trim().orEmpty()
                if (text.length < 2) { toast("متن خالی است"); return@setOnClickListener }
                Thread {
                    val id = app.db.addText("متن جایگذاری‌شده", text)
                    runOnUiThread {
                        pasteInput?.setText("")
                        type = "text"
                        tabs.getTabAt(0)?.select()
                        reload()
                        try {
                            Conversion.start(this@LibraryActivity, id)
                            toast("تبدیل به صوت شروع شد")
                        } catch (e: Throwable) {
                            toast("شروع تبدیل ممکن نشد")
                        }
                    }
                }.start()
            }
        } catch (e: Throwable) {
            android.util.Log.e("Library", "paste bind", e)
        }
'''
        if 'list.adapter = Adapter()' in lt:
            lt = lt.replace('list.adapter = Adapter()', 'list.adapter = Adapter()\n' + bind, 1)
        lib.write_text(lt, encoding='utf-8')
        print('LibraryActivity paste')

bg = proj / 'app/build.gradle.kts'
if bg.exists():
    t = bg.read_text(encoding='utf-8')
    for old, new in [
        ('versionCode = 53', 'versionCode = 54'),
        ('versionCode = 52', 'versionCode = 54'),
        ('versionName = "5.3"', 'versionName = "5.4"'),
        ('versionName = "5.2"', 'versionName = "5.4"'),
    ]:
        t = t.replace(old, new)
    bg.write_text(t, encoding='utf-8')
    print('version -> 5.4')

print('ALL v5.4 PATCHES DONE')
