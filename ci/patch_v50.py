#!/usr/bin/env python3
"""Apply v5.0 features onto full KhanshgarZende source tree."""
from pathlib import Path
import os
import shutil

proj = Path(os.environ['PROJ'])
src = proj / 'app/src/main/java/com/example/khanshgarzende'
res = proj / 'app/src/main/res'
manifest = proj / 'app/src/main/AndroidManifest.xml'

# 1) ReadAloudService
service_src = Path(__file__).resolve().parent.parent / 'app/src/main/java/com/example/khanshgarzende/ReadAloudService.kt'
if not service_src.exists():
    service_src = Path('app/src/main/java/com/example/khanshgarzende/ReadAloudService.kt')
if service_src.exists():
    shutil.copy2(service_src, src / 'ReadAloudService.kt')
    print('ReadAloudService.kt injected')
else:
    print('WARNING: ReadAloudService.kt missing')

xml_dir = res / 'xml'
xml_dir.mkdir(parents=True, exist_ok=True)
xml_src = Path(__file__).resolve().parent.parent / 'app/src/main/res/xml/read_aloud_service.xml'
if not xml_src.exists():
    xml_src = Path('app/src/main/res/xml/read_aloud_service.xml')
if xml_src.exists():
    shutil.copy2(xml_src, xml_dir / 'read_aloud_service.xml')
else:
    (xml_dir / 'read_aloud_service.xml').write_text('''<?xml version="1.0" encoding="utf-8"?>
<accessibility-service xmlns:android="http://schemas.android.com/apk/res/android"
    android:accessibilityEventTypes="typeViewClicked|typeViewFocused|typeWindowStateChanged|typeViewTextSelectionChanged|typeWindowContentChanged"
    android:accessibilityFeedbackType="feedbackSpoken"
    android:accessibilityFlags="flagReportViewIds|flagRetrieveInteractiveWindows|flagRequestEnhancedWebAccessibility|flagIncludeNotImportantViews"
    android:canRetrieveWindowContent="true"
    android:description="@string/read_aloud_service_description"
    android:notificationTimeout="100"
    android:settingsActivity="com.example.khanshgarzende.SettingsActivity" />
''', encoding='utf-8')
print('accessibility xml ok')

# 2) Manifest
man = manifest.read_text(encoding='utf-8')
if 'ReadAloudService' not in man:
    block = '''
        <service
            android:name=".ReadAloudService"
            android:exported="true"
            android:label="@string/read_aloud_service_label"
            android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE">
            <intent-filter>
                <action android:name="android.accessibilityservice.AccessibilityService" />
            </intent-filter>
            <meta-data
                android:name="android.accessibilityservice"
                android:resource="@xml/read_aloud_service" />
        </service>
'''
    man = man.replace('    </application>', block + '    </application>')
    manifest.write_text(man, encoding='utf-8')
    print('manifest updated')

# 3) Strings
strings_path = res / 'values/strings.xml'
st = strings_path.read_text(encoding='utf-8')
if 'read_aloud_service_label' not in st:
    insert = '''
    <string name="read_aloud_service_label">خواندن با صدای بلند – خوانشگر زنده</string>
    <string name="read_aloud_service_description">با روشن کردن این سرویس، خوانشگر زنده می‌تواند متن‌های پیام‌رسان‌ها (تلگرام، روبیکا، سروش، بله و …) و سایر برنامه‌ها را با صدای طبیعی خود برنامه بخواند.</string>
'''
    st = st.replace('</resources>', insert + '</resources>')
    strings_path.write_text(st, encoding='utf-8')
    print('strings added')

# 4) Prefs
prefs_path = src / 'Prefs.kt'
if prefs_path.exists():
    prefs = prefs_path.read_text(encoding='utf-8')
    if 'readMode' not in prefs:
        extra = '''
    var readMode: String
        get() = sp.getString("read_mode", "paragraph") ?: "paragraph"
        set(v) = sp.edit().putString("read_mode", v).apply()

    var batchScan: Boolean
        get() = sp.getBoolean("batch_scan", false)
        set(v) = sp.edit().putBoolean("batch_scan", v).apply()

    var autoCleanText: Boolean
        get() = sp.getBoolean("auto_clean_text", true)
        set(v) = sp.edit().putBoolean("auto_clean_text", v).apply()
'''
        idx = prefs.rfind('}')
        if idx > 0:
            prefs = prefs[:idx] + extra + '\n' + prefs[idx:]
            prefs_path.write_text(prefs, encoding='utf-8')
            print('Prefs extended')

# 5) VoicePacks EN+AR
vp_path = src / 'VoicePacks.kt'
if vp_path.exists():
    vp = vp_path.read_text(encoding='utf-8')
    if 'en_lessac' not in vp:
        old = '''    val PACKS = listOf(
        Pack("amir", "امیر (صدای طبیعی مرد)", "vits-piper-fa_IR-amir-medium-int8", 21),
        Pack("gyro", "ژیرو (صدای طبیعی مرد)", "vits-piper-fa_IR-gyro-medium-int8", 21),
        Pack("reza", "رضا (صدای طبیعی مرد)", "vits-piper-fa_IR-reza_ibrahim-medium-int8", 21),
        Pack("ganji", "گنجی (صدای طبیعی مرد)", "vits-piper-fa_IR-ganji-medium-int8", 21),
    )'''
        new = '''    val PACKS = listOf(
        Pack("amir", "امیر (فارسی مرد)", "vits-piper-fa_IR-amir-medium-int8", 21),
        Pack("gyro", "ژیرو (فارسی مرد)", "vits-piper-fa_IR-gyro-medium-int8", 21),
        Pack("reza", "رضا (فارسی مرد)", "vits-piper-fa_IR-reza_ibrahim-medium-int8", 21),
        Pack("ganji", "گنجی (فارسی مرد)", "vits-piper-fa_IR-ganji-medium-int8", 21),
        Pack("en_lessac", "Lessac (انگلیسی زن – آفلاین)", "vits-piper-en_US-lessac-medium", 63),
        Pack("en_amy", "Amy (انگلیسی زن – آفلاین)", "vits-piper-en_US-amy-medium", 63),
        Pack("ar_kareem", "کریم (عربی مرد – آفلاین)", "vits-piper-ar_JO-kareem-medium", 63),
    )'''
        if old in vp:
            vp_path.write_text(vp.replace(old, new), encoding='utf-8')
            print('VoicePacks EN+AR added')
        else:
            print('VoicePacks pattern skip')

# 6) PersianText cleaner
pt_path = src / 'PersianText.kt'
if pt_path.exists():
    pt = pt_path.read_text(encoding='utf-8')
    if 'fun cleanOcrText' not in pt:
        cleaner = '''
    fun cleanOcrText(input: String): String {
        var s = normalize(input)
        s = s.replace(Regex("[\\u0000-\\u0008\\u000B\\u000C\\u000E-\\u001F]"), "")
        s = s.replace(Regex("[|¦¬~^`]+"), " ")
        s = s.replace(Regex("\\s+([.,!?;:،؛؟])"), "$1")
        s = s.replace(Regex("([.,!?;:،؛؟])(\\S)"), "$1 $2")
        s = s.replace(Regex("[ \\t\\x0B\\f]+"), " ")
        s = s.replace(Regex("\\n{3,}"), "\\n\\n")
        s = s.replace(Regex("([\\u0600-\\u06FF])([A-Za-z])"), "$1 $2")
        s = s.replace(Regex("([A-Za-z])([\\u0600-\\u06FF])"), "$1 $2")
        return s.trim()
    }

    fun splitForReadMode(text: String, mode: String): List<String> {
        val t = text.trim()
        if (t.isEmpty()) return listOf()
        return when (mode) {
            "word" -> t.split(Regex("\\s+")).filter { it.isNotBlank() }
            "line" -> t.split(Regex("\\r?\\n")).map { it.trim() }.filter { it.isNotEmpty() }
            else -> {
                val parts = t.split(Regex("\\n\\s*\\n|\\r\\n\\s*\\r\\n"))
                if (parts.size > 1) parts.map { it.trim() }.filter { it.isNotEmpty() }
                else t.split(Regex("(?<=[.!?؟۔])\\s+")).map { it.trim() }.filter { it.isNotEmpty() }
            }
        }
    }
'''
        idx = pt.rfind('}')
        if idx > 0:
            pt_path.write_text(pt[:idx] + cleaner + '\n' + pt[idx:], encoding='utf-8')
            print('PersianText cleaner added')

# 7) TextViewer page turn + clean
tv_path = src / 'TextViewerActivity.kt'
if tv_path.exists():
    tv = tv_path.read_text(encoding='utf-8')
    if 'playPageTurnSound' not in tv:
        if 'ToneGenerator' not in tv:
            tv = tv.replace(
                'import android.os.Bundle\n',
                'import android.media.AudioManager\nimport android.media.ToneGenerator\nimport android.os.Bundle\nimport android.os.Handler\nimport android.os.Looper\n',
            )
        marker = 'private fun read(p: Int, text: String)'
        if marker in tv:
            i = tv.index(marker)
            rest = tv[i:]
            rest2 = rest
            if 'val speakText = text.ifBlank' in rest2:
                rest2 = rest2.replace(
                    'val speakText = text.ifBlank { "این صفحه متنی ندارد." }',
                    'val pageAnnounce = "صفحهٔ " + fa(p + 1) + ". "\n        val raw = text.ifBlank { "این صفحه متنی ندارد." }\n        val body = if (app.prefs.autoCleanText) PersianText.cleanOcrText(raw) else raw\n        val speakText = pageAnnounce + body',
                    1,
                )
            if 'showPage(p + 1, true)' in rest2 and 'playPageTurnSound' not in rest2:
                rest2 = rest2.replace(
                    'if (!app.prefs.paginate && p + 1 < doc.count) {\n                    showPage(p + 1, true)',
                    'if (!app.prefs.paginate && p + 1 < doc.count) {\n                    playPageTurnSound()\n                    Handler(Looper.getMainLooper()).postDelayed({\n                        if (reading && page == p) showPage(p + 1, true)\n                    }, 280)',
                    1,
                )
            helper = '''    private fun playPageTurnSound() {
        try {
            val tg = ToneGenerator(AudioManager.STREAM_MUSIC, 70)
            tg.startTone(ToneGenerator.TONE_PROP_BEEP2, 120)
            Handler(Looper.getMainLooper()).postDelayed({ try { tg.release() } catch (_: Throwable) {} }, 300)
        } catch (_: Throwable) {}
    }

    '''
            rest2 = helper + rest2
            tv_path.write_text(tv[:i] + rest2, encoding='utf-8')
            print('TextViewer patched')

# 8) SpeechManager faster
sm_path = src / 'SpeechManager.kt'
if sm_path.exists():
    sm = sm_path.read_text(encoding='utf-8')
    sm2 = sm.replace('Executors.newFixedThreadPool(4) else null', 'Executors.newFixedThreadPool(8) else null')
    sm2 = sm2.replace('if (pool != null) 600 else 250', 'if (pool != null) 1200 else 400')
    sm2 = sm2.replace('writerRate / 3), writerRate) // مکث بین صفحه‌ها', 'writerRate / 10), writerRate) // مکث کوتاه بین صفحه‌ها')
    sm2 = sm2.replace('Executors.newFixedThreadPool(3)', 'Executors.newFixedThreadPool(5)')
    if sm2 != sm:
        sm_path.write_text(sm2, encoding='utf-8')
        print('SpeechManager faster')

# 9) Version 5.0
bg_path = proj / 'app/build.gradle.kts'
if bg_path.exists():
    bg = bg_path.read_text(encoding='utf-8')
    bg2 = bg
    for old, new in [
        ('versionCode = 3', 'versionCode = 50'),
        ('versionCode = 4', 'versionCode = 50'),
        ('versionCode = 40', 'versionCode = 50'),
        ('versionName = "3.0"', 'versionName = "5.0"'),
        ('versionName = "3.1"', 'versionName = "5.0"'),
        ('versionName = "4.0"', 'versionName = "5.0"'),
    ]:
        bg2 = bg2.replace(old, new)
    bg_path.write_text(bg2, encoding='utf-8')
    print('version -> 5.0')

print('ALL v5.0 PATCHES DONE')
