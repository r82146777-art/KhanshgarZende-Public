#!/usr/bin/env python3
"""Apply v4.0 features onto full KhanshgarZende source tree.
Priority: Read Aloud Accessibility Service + previous v3.1 improvements.
"""
from pathlib import Path
import os
import shutil

proj = Path(os.environ['PROJ'])
src = proj / 'app/src/main/java/com/example/khanshgarzende'
res = proj / 'app/src/main/res'
manifest = proj / 'app/src/main/AndroidManifest.xml'

# ---------- 1) Inject ReadAloudService.kt ----------
service_src = Path(__file__).resolve().parent.parent / 'app/src/main/java/com/example/khanshgarzende/ReadAloudService.kt'
if not service_src.exists():
    service_src = Path('app/src/main/java/com/example/khanshgarzende/ReadAloudService.kt')
if service_src.exists():
    dest = src / 'ReadAloudService.kt'
    shutil.copy2(service_src, dest)
    print('ReadAloudService.kt injected')
else:
    print('WARNING: ReadAloudService.kt not found in overlay')

# ---------- 2) Inject accessibility config xml ----------
xml_src = Path(__file__).resolve().parent.parent / 'app/src/main/res/xml/read_aloud_service.xml'
if not xml_src.exists():
    xml_src = Path('app/src/main/res/xml/read_aloud_service.xml')
xml_dir = res / 'xml'
xml_dir.mkdir(parents=True, exist_ok=True)
if xml_src.exists():
    shutil.copy2(xml_src, xml_dir / 'read_aloud_service.xml')
    print('read_aloud_service.xml injected')
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
    print('read_aloud_service.xml written (fallback)')

# ---------- 3) Update AndroidManifest ----------
man = manifest.read_text(encoding='utf-8')
if 'ReadAloudService' not in man:
    service_block = '''
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
    man = man.replace('    </application>', service_block + '    </application>')
    manifest.write_text(man, encoding='utf-8')
    print('AndroidManifest updated with ReadAloudService')
else:
    print('AndroidManifest already has ReadAloudService')

# ---------- 4) Add strings ----------
strings_path = res / 'values/strings.xml'
st = strings_path.read_text(encoding='utf-8')
if 'read_aloud_service_label' not in st:
    insert = '''
    <string name="read_aloud_service_label">خواندن با صدای بلند – خوانشگر زنده</string>
    <string name="read_aloud_service_description">با روشن کردن این سرویس، خوانشگر زنده می‌تواند متن‌های پیام‌رسان‌ها (تلگرام، روبیکا، سروش، بله و …) و سایر برنامه‌ها را با صدای طبیعی خود برنامه بخواند. پس از فعال‌سازی، روی متن مورد نظر بزنید تا خوانده شود.</string>
'''
    st = st.replace('</resources>', insert + '</resources>')
    strings_path.write_text(st, encoding='utf-8')
    print('strings added')

# ---------- 5) Previous v3.1 patches ----------
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
                    'val pageAnnounce = "صفحهٔ " + fa(p + 1) + ". "\n        val body = text.ifBlank { "این صفحه متنی ندارد." }\n        val speakText = pageAnnounce + body',
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
            tv = tv[:i] + rest2
            tv_path.write_text(tv, encoding='utf-8')
            print('TextViewer patched (page turn)')

sm_path = src / 'SpeechManager.kt'
if sm_path.exists():
    sm = sm_path.read_text(encoding='utf-8')
    sm2 = sm.replace('Executors.newFixedThreadPool(4) else null', 'Executors.newFixedThreadPool(6) else null')
    sm2 = sm2.replace('if (pool != null) 600 else 250', 'if (pool != null) 900 else 320')
    sm2 = sm2.replace('writerRate / 3), writerRate) // مکث بین صفحه‌ها', 'writerRate / 8), writerRate) // مکث کوتاه بین صفحه‌ها')
    sm2 = sm2.replace('Executors.newFixedThreadPool(3)', 'Executors.newFixedThreadPool(4)')
    if sm2 != sm:
        sm_path.write_text(sm2, encoding='utf-8')
        print('SpeechManager speed patched')

bg_path = proj / 'app/build.gradle.kts'
if bg_path.exists():
    bg = bg_path.read_text(encoding='utf-8')
    bg2 = bg
    for old, new in [
        ('versionCode = 3', 'versionCode = 40'),
        ('versionCode = 4', 'versionCode = 40'),
        ('versionName = "3.0"', 'versionName = "4.0"'),
        ('versionName = "3.1"', 'versionName = "4.0"'),
    ]:
        bg2 = bg2.replace(old, new)
    bg_path.write_text(bg2, encoding='utf-8')
    print('version -> 4.0')

print('ALL v4.0 PATCHES DONE')
