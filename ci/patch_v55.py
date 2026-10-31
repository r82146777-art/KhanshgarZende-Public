#!/usr/bin/env python3
"""v5.5: voice guide, conversion, OCR clean, scene-only camera, API key, app filter."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parent
for name in ('patch_v50.py', 'patch_v51.py', 'patch_v52.py', 'patch_v53.py', 'patch_v54.py', 'patch_v54b.py', 'patch_v54c.py'):
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
    extra = ''
    if 'readAllApps' not in t:
        extra += '''
    var readAllApps: Boolean
        get() = sp.getBoolean("read_all_apps", true)
        set(v) = sp.edit().putBoolean("read_all_apps", v).apply()
    var allowedPackages: String
        get() = sp.getString("allowed_packages", "") ?: ""
        set(v) = sp.edit().putString("allowed_packages", v).apply()
    fun isPackageAllowed(pkg: String): Boolean {
        if (readAllApps) return true
        val set = allowedPackages.split(',').map { it.trim() }.filter { it.isNotEmpty() }.toSet()
        if (set.isEmpty()) return true
        return pkg in set
    }
'''
    if 'apiKey' not in t:
        extra += '''
    var apiKey: String
        get() = azureKey
        set(v) { azureKey = v }
'''
    if extra:
        idx = t.rfind('}')
        prefs.write_text(t[:idx] + extra + '\n' + t[idx:], encoding='utf-8')
        print('Prefs v55')

pt = src / 'PersianText.kt'
if pt.exists():
    t = pt.read_text(encoding='utf-8')
    if 'fun cleanOcrText' not in t:
        cleaner = '''
    fun cleanOcrText(input: String): String {
        if (input.isBlank()) return ""
        var s = input
        s = s.replace('ي', 'ی').replace('ك', 'ک').replace('ة', 'ه').replace('ؤ', 'و').replace('إ', 'ا').replace('أ', 'ا')
        s = s.map { c ->
            when (c) {
                in '٠'..'٩' -> ('0'.code + (c.code - '٠'.code)).toChar()
                in '۰'..'۹' -> ('0'.code + (c.code - '۰'.code)).toChar()
                else -> c
            }
        }.joinToString("")
        s = s.replace(Regex("[|¦_~`^]+"), " ")
        s = s.replace(Regex("\\s+([،,؛;:.!?؟])"), "$1")
        s = s.replace(Regex("([،,؛;:.!?؟])(\\S)"), "$1 $2")
        val lines = s.lines().map { it.trim() }.filter { it.isNotEmpty() }
        s = lines.filter { letterCount(it) > 1 || it.length >= 4 }.joinToString("\n")
        s = s.replace(Regex("\\n{3,}"), "\n\n").replace(Regex(" {2,}"), " ")
        return s.trim()
    }
'''
        idx = t.rfind('}')
        pt.write_text(t[:idx] + cleaner + '\n' + t[idx:], encoding='utf-8')
        print('PersianText cleanOcrText')
    else:
        t2 = re.sub(
            r'fun cleanOcrText\(input: String\): String \{[\s\S]*?\n    \}',
            '''fun cleanOcrText(input: String): String {
        if (input.isBlank()) return ""
        var s = input
        s = s.replace('ي', 'ی').replace('ك', 'ک').replace('ة', 'ه').replace('ؤ', 'و').replace('إ', 'ا').replace('أ', 'ا')
        s = s.map { c ->
            when (c) {
                in '٠'..'٩' -> ('0'.code + (c.code - '٠'.code)).toChar()
                in '۰'..'۹' -> ('0'.code + (c.code - '۰'.code)).toChar()
                else -> c
            }
        }.joinToString("")
        s = s.replace(Regex("[|¦_~`^]+"), " ")
        s = s.replace(Regex("\\s+([،,؛;:.!?؟])"), "$1")
        s = s.replace(Regex("([،,؛;:.!?؟])(\\S)"), "$1 $2")
        val lines = s.lines().map { it.trim() }.filter { it.isNotEmpty() }
        s = lines.filter { letterCount(it) > 1 || it.length >= 4 }.joinToString("\n")
        s = s.replace(Regex("\\n{3,}"), "\n\n").replace(Regex(" {2,}"), " ")
        return s.trim()
    }''',
            t,
            count=1,
        )
        if t2 != t:
            pt.write_text(t2, encoding='utf-8')
            print('PersianText cleaner upgraded')

te = src / 'TextExtractor.kt'
if te.exists():
    t = te.read_text(encoding='utf-8')
    if 'ocrEmptyPdfPages' not in t:
        helper = '''
    private fun ocrEmptyPdfPages(f: File, pages: MutableList<String>, progress: (String) -> Unit) {
        val emptyIdx = pages.indices.filter { PersianText.letterCount(pages[it]) < 20 }
        if (emptyIdx.isEmpty()) return
        val maxOcr = emptyIdx.take(80)
        try {
            val pfd = android.os.ParcelFileDescriptor.open(f, android.os.ParcelFileDescriptor.MODE_READ_ONLY)
            android.graphics.pdf.PdfRenderer(pfd).use { renderer ->
                for (i in maxOcr) {
                    if (i >= renderer.pageCount) break
                    progress("تشخیص متن صفحهٔ تصویری " + PersianText.faDigits(i + 1))
                    renderer.openPage(i).use { page ->
                        val scale = 2
                        val bmp = android.graphics.Bitmap.createBitmap(page.width * scale, page.height * scale, android.graphics.Bitmap.Config.ARGB_8888)
                        page.render(bmp, null, null, android.graphics.pdf.PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                        try {
                            var text = App.instance.ocr.recognize(bmp, false).text
                            text = try { PersianText.cleanOcrText(text) } catch (_: Throwable) { PersianText.normalize(text) }
                            if (PersianText.letterCount(text) >= 10) pages[i] = text
                        } catch (_: Throwable) {}
                        bmp.recycle()
                    }
                }
            }
            pfd.close()
        } catch (e: Throwable) {
            android.util.Log.e("TextExtractor", "ocrEmptyPdfPages", e)
        }
    }
'''
        idx = t.rfind('}')
        t = t[:idx] + helper + '\n' + t[idx:]
        if 'val pages = pdfPages(tmp, progress)' in t:
            t = t.replace(
                'val pages = pdfPages(tmp, progress)',
                'val pages = pdfPages(tmp, progress).toMutableList()\n'
                '            if (pages.count { PersianText.letterCount(it) < 20 } > pages.size / 2)\n'
                '                ocrEmptyPdfPages(tmp, pages, progress)',
            )
        te.write_text(t, encoding='utf-8')
        print('TextExtractor PDF OCR')

cs = src / 'ConversionService.kt'
if cs.exists():
    t = cs.read_text(encoding='utf-8')
    if 'preOcrPages' not in t and 'پیش‌پردازش OCR' not in t:
        needle = 'Conversion.state.value = ConvState.Running(item.title, 0, doc.count)'
        inject = '''Conversion.state.value = ConvState.Running(item.title, 0, doc.count)
            // preOcrPages
            try {
                for (i in 0 until doc.count) {
                    if (Conversion.cancelRequested) break
                    if (doc.needsOcr(i)) {
                        nm.notify(1, notif("تشخیص متن صفحهٔ " + PersianText.faDigits(i + 1) + " از " + PersianText.faDigits(doc.count), i, doc.count))
                        try { doc.page(i) } catch (_: Throwable) {}
                    }
                }
            } catch (e: Throwable) { Log.e("ConversionService", "preOcr", e) }
'''
        if needle in t:
            t = t.replace(needle, inject, 1)
    t = t.replace(
        'finish(ConvState.Failed(if (Conversion.cancelRequested) "تبدیل لغو شد" else "متنی برای تبدیل به صوت وجود ندارد"))',
        'finish(ConvState.Failed(if (Conversion.cancelRequested) "تبدیل لغو شد" else "تبدیل ناموفق بود. صدای آفلاین را انتخاب کنید یا اینترنت/کلید API را بررسی کنید"))',
    )
    cs.write_text(t, encoding='utf-8')
    print('ConversionService')

sm = src / 'SpeechManager.kt'
if sm.exists():
    t = sm.read_text(encoding='utf-8')
    t2 = t.replace(
        'val pool = if (isOnline && onlineConfigured) Executors.newFixedThreadPool(6) else null',
        'val useOnline = isOnline && onlineConfigured\n'
        '        if (isOnline && !onlineConfigured) Log.w(TAG, "online voice without API key; using offline")\n'
        '        val pool = if (useOnline) Executors.newFixedThreadPool(6) else null',
    )
    if t2 != t:
        sm.write_text(t2, encoding='utf-8')
        print('SpeechManager online guard')

cam = src / 'CameraActivity.kt'
if cam.exists():
    t = cam.read_text(encoding='utf-8')
    t = t.replace(
        '''val quick = ocr.recognize(bmp, true)
            if (forceRead || quick.goodWords >= 3) {
                forceRead = false
                readTextHighQuality(bmp)
                return
            }
            val sc = scene!!.describe(bmp)
            if (sc.maybeText && quick.goodWords >= 1) { readTextHighQuality(bmp); return }
            if (!app.prefs.describeScene) { mode = Mode.SCANNING; return }
            describeScene(sc)''',
        '''forceRead = false
            if (!app.prefs.describeScene) {
                setStatus("تشخیص محیط خاموش است. از تنظیمات روشن کنید.")
                mode = Mode.SCANNING
                return
            }
            val sc = scene!!.describe(bmp)
            describeScene(sc)''',
    )
    t = t.replace(
        '''val hint = when {
            s.dark -> ""
            s.maybeText -> " به نظر می‌رسد نوشته‌ای جلوی دوربین است. گوشی را حدود سی سانتی‌متر بالای متن، صاف و ثابت نگه دارید."
            sceneCount % 3 == 1 -> " اگر می‌خواهید متن را برایتان بخوانم، لطفاً دوربین را روی کتاب یا نوشته بگیرید."
            else -> ""
        }''',
        '''val hint = when {
            s.dark -> " نور را بیشتر کنید."
            else -> ""
        }''',
    )
    for a, b in [
        ('speakThen("دوربین باز شد. دوربین را به سمت متن یا اطراف بگیرید.")', 'speakThen("دوربین تشخیص اشیا باز شد. دوربین را به اطراف بگیرید.")'),
        ('speakThen("دوربین باز شد. برای عکس دکمه گرفتن عکس را بزنید.")', 'speakThen("دوربین تشخیص اشیا باز شد. برای عکس دکمه گرفتن عکس را بزنید.")'),
    ]:
        t = t.replace(a, b)
    cam.write_text(t, encoding='utf-8')
    print('CameraActivity objects-only')

sd = src / 'SceneDescriber.kt'
if sd.exists():
    t = sd.read_text(encoding='utf-8')
    t = t.replace('parts.add("جلوی شما احتمالاً $joined دیده می‌شود")', 'parts.add("جلوی شما $joined دیده می‌شود")')
    if 'dominantColorHint' not in t:
        t = t.replace('val light = brightness(bmp)', 'val light = brightness(bmp)\n        val colorHint = dominantColorHint(bmp)')
        t = t.replace(
            'parts.add("جلوی شما $joined دیده می‌شود")',
            'val col = if (colorHint.isNotEmpty()) " با رنگ $colorHint" else ""\n            parts.add("جلوی شما $joined$col دیده می‌شود")',
        )
        helper = '''
    private fun dominantColorHint(bmp: Bitmap): String {
        return try {
            val w = 16; val h = 16
            val small = Bitmap.createScaledBitmap(bmp, w, h, true)
            var r = 0L; var g = 0L; var b = 0L; var n = 0
            for (y in 0 until h) for (x in 0 until w) {
                val c = small.getPixel(x, y)
                r += (c shr 16) and 0xff; g += (c shr 8) and 0xff; b += c and 0xff; n++
            }
            if (small !== bmp) small.recycle()
            if (n == 0) return ""
            r /= n; g /= n; b /= n
            when {
                r > 180 && g > 180 && b > 180 -> "روشن"
                r < 50 && g < 50 && b < 50 -> "تیره"
                r > g + 30 && r > b + 30 -> "قرمز یا نارنجی"
                g > r + 30 && g > b + 30 -> "سبز"
                b > r + 30 && b > g + 30 -> "آبی"
                r > 150 && g > 120 && b < 100 -> "زرد یا قهوه‌ای"
                else -> ""
            }
        } catch (_: Throwable) { "" }
    }
'''
        idx = t.rfind('}')
        t = t[:idx] + helper + '\n' + t[idx:]
    sd.write_text(t, encoding='utf-8')
    print('SceneDescriber')

bs = src / 'BatchScanActivity.kt'
if bs.exists():
    t = bs.read_text(encoding='utf-8')
    t2 = re.sub(
        r'private fun setStatus\(s: String\) = runOnUiThread \{\s*status\.text = s;?\s*status\.announceForAccessibility\(s\)\s*\}',
        'private fun setStatus(s: String) = runOnUiThread {\n'
        '        status.text = s; status.announceForAccessibility(s)\n'
        '        try { if (app.prefs.voiceGuide && s.length in 8..180) app.speech.speak(s) } catch (_: Throwable) {}\n'
        '    }',
        t,
        count=1,
    )
    t2 = t2.replace(
        'setStatus("آماده. صفحه را بگیرید و «گرفتن صفحه» را بزنید.")',
        'setStatus("آماده. گوشی را حدود سی سانتی‌متر بالای صفحه صاف بگیرید و دکمه گرفتن صفحه را بزنید.")',
    )
    bs.write_text(t2, encoding='utf-8')
    print('BatchScan voice')

ra = src / 'ReadAloudService.kt'
if ra.exists():
    t = ra.read_text(encoding='utf-8')
    if 'isPackageAllowed' not in t:
        t = t.replace(
            'override fun onAccessibilityEvent(event: AccessibilityEvent?) {\n        if (event == null) return\n',
            'override fun onAccessibilityEvent(event: AccessibilityEvent?) {\n'
            '        if (event == null) return\n'
            '        try {\n'
            '            val pkg = event.packageName?.toString() ?: ""\n'
            '            val prefs = try { Prefs(applicationContext) } catch (_: Throwable) { null }\n'
            '            if (prefs != null && !prefs.isPackageAllowed(pkg)) return\n'
            '        } catch (_: Throwable) {}\n',
        )
        ra.write_text(t, encoding='utf-8')
        print('ReadAloud filter')

lay = res / 'layout/activity_settings.xml'
if lay.exists():
    lx = lay.read_text(encoding='utf-8')
    if 'sw_read_all_apps' not in lx:
        block = '''
    <TextView style="@style/Label" android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:layout_marginTop="16dp" android:text="کلید API و دسترس‌پذیری" android:textStyle="bold"
        android:textSize="18sp" android:accessibilityHeading="true" />
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
        android:textSize="14sp"
        android:text="کلید سرویس گفتار مایکروسافت برای صداهای آنلاین دلارا و فرید. بدون کلید از صدای آفلاین استفاده می‌شود." />
    <EditText android:id="@+id/api_key_extra"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:hint="کلید API (اختیاری)" android:inputType="textPassword" android:minHeight="48dp" />
    <EditText android:id="@+id/api_region_extra"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:hint="منطقه (مثلاً westeurope)" android:inputType="text" android:minHeight="48dp" />
    <androidx.appcompat.widget.SwitchCompat
        android:id="@+id/sw_read_all_apps"
        android:layout_width="match_parent" android:layout_height="64dp"
        android:textSize="17sp" android:text="خواندن با صدای بلند در همه برنامه‌ها" />
    <com.google.android.material.button.MaterialButton
        android:id="@+id/btn_pick_apps"
        android:layout_width="match_parent" android:layout_height="wrap_content"
        android:text="انتخاب برنامه‌های مجاز" />
'''
        idx = lx.rfind('</LinearLayout>')
        if idx > 0:
            lay.write_text(lx[:idx] + block + '\n' + lx[idx:], encoding='utf-8')
            print('settings layout')

sa = src / 'SettingsActivity.kt'
if sa.exists():
    st = sa.read_text(encoding='utf-8')
    if 'sw_read_all_apps' not in st:
        method = '''
    private fun bindAccessibilityAndApiV55() {
        try {
            val keyBox = findViewById<EditText>(R.id.api_key_extra)
            val regionBox = findViewById<EditText>(R.id.api_region_extra)
            keyBox?.setText(p.azureKey)
            regionBox?.setText(p.azureRegion)
            keyBox?.setOnFocusChangeListener { _, has ->
                if (!has) p.azureKey = keyBox.text?.toString()?.trim().orEmpty()
            }
            regionBox?.setOnFocusChangeListener { _, has ->
                if (!has) p.azureRegion = regionBox.text?.toString()?.trim().orEmpty().ifBlank { "westeurope" }
            }
            findViewById<SwitchCompat>(R.id.sw_read_all_apps)?.let { sw ->
                sw.isChecked = try { p.readAllApps } catch (_: Throwable) { true }
                sw.setOnCheckedChangeListener { _, c ->
                    try { p.readAllApps = c } catch (_: Throwable) {}
                    findViewById<View>(R.id.btn_pick_apps)?.isEnabled = !c
                }
                findViewById<View>(R.id.btn_pick_apps)?.isEnabled = !sw.isChecked
            }
            findViewById<Button>(R.id.btn_pick_apps)?.setOnClickListener { showAppPicker() }
        } catch (e: Throwable) {
            android.util.Log.e("Settings", "bindAccessibilityAndApiV55", e)
        }
    }

    private fun showAppPicker() {
        try {
            val pm = packageManager
            val apps = pm.getInstalledApplications(0)
                .filter { pm.getLaunchIntentForPackage(it.packageName) != null }
                .sortedBy { it.loadLabel(pm).toString() }
            val labels = apps.map { it.loadLabel(pm).toString() + " (" + it.packageName + ")" }.toTypedArray()
            val pkgs = apps.map { it.packageName }.toTypedArray()
            val selected = try { p.allowedPackages.split(',').map { it.trim() }.filter { it.isNotEmpty() }.toMutableSet() } catch (_: Throwable) { mutableSetOf() }
            val checked = BooleanArray(pkgs.size) { pkgs[it] in selected }
            androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("برنامه‌های مجاز")
                .setMultiChoiceItems(labels, checked) { _, which, isChecked ->
                    if (isChecked) selected.add(pkgs[which]) else selected.remove(pkgs[which])
                }
                .setPositiveButton("ذخیره") { _, _ ->
                    p.allowedPackages = selected.joinToString(",")
                    p.readAllApps = false
                    toast("ذخیره شد. تعداد: " + selected.size)
                    findViewById<SwitchCompat>(R.id.sw_read_all_apps)?.isChecked = false
                }
                .setNegativeButton("انصراف", null)
                .show()
        } catch (e: Throwable) {
            toast("لیست برنامه‌ها در دسترس نیست")
        }
    }

'''
        if 'bindExtraSettingsV54()' in st:
            st = st.replace('bindExtraSettingsV54()', 'bindExtraSettingsV54()\n        bindAccessibilityAndApiV55()')
        elif 'updateBoxes()' in st:
            st = st.replace('updateBoxes()', 'bindAccessibilityAndApiV55()\n        updateBoxes()', 1)
        idx = st.rfind('}')
        st = st[:idx] + method + '\n' + st[idx:]
        if 'import android.widget.EditText' not in st:
            st = st.replace('import android.widget.Button', 'import android.widget.Button\nimport android.widget.EditText')
        sa.write_text(st, encoding='utf-8')
        print('SettingsActivity')

man = proj / 'app/src/main/AndroidManifest.xml'
if man.exists():
    mt = man.read_text(encoding='utf-8')
    if 'QUERY_ALL_PACKAGES' not in mt:
        mt = mt.replace(
            '<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />',
            '<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />\n'
            '    <uses-permission android:name="android.permission.QUERY_ALL_PACKAGES" tools:ignore="QueryAllPackagesPermission" />',
        )
        if 'xmlns:tools' not in mt:
            mt = mt.replace(
                'xmlns:android="http://schemas.android.com/apk/res/android"',
                'xmlns:android="http://schemas.android.com/apk/res/android"\n    xmlns:tools="http://schemas.android.com/tools"',
            )
        man.write_text(mt, encoding='utf-8')
        print('manifest')

bg = proj / 'app/build.gradle.kts'
if bg.exists():
    t = bg.read_text(encoding='utf-8')
    for a, b in [('versionCode = 54', 'versionCode = 55'), ('versionCode = 53', 'versionCode = 55'),
                 ('versionName = "5.4"', 'versionName = "5.5"'), ('versionName = "5.3"', 'versionName = "5.5"')]:
        t = t.replace(a, b)
    bg.write_text(t, encoding='utf-8')
    print('version -> 5.5')

print('ALL v5.5 PATCHES DONE')
