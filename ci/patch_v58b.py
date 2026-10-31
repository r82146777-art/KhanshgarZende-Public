#!/usr/bin/env python3
"""v5.8b: fix corrupted PACKS and SettingsActivity binding from v58."""
from pathlib import Path
import os, re, subprocess, sys

root = Path(__file__).resolve().parent
p57 = root / 'patch_v58.py'
if p57.exists():
    r = subprocess.run([sys.executable, str(p57)], check=False)
    print('patch_v58 exit', r.returncode)

proj = Path(os.environ['PROJ'])
src = proj / 'app/src/main/java/com/example/khanshgarzende'

vp = src / 'VoicePacks.kt'
vt = vp.read_text(encoding='utf-8')
vt2 = re.sub(
    r'val PACKS = listOf\([\s\S]*?\n    \)',
    '''val PACKS = listOf(
        Pack("amir", "امیر – مرد (آفلاین Piper)", "vits-piper-fa_IR-amir-medium-int8", 21),
        Pack("reza", "رضا – مرد (آفلاین Piper)", "vits-piper-fa_IR-reza_ibrahim-medium-int8", 21),
        Pack("ganji", "گنجی – مرد (آفلاین Piper)", "vits-piper-fa_IR-ganji-medium-int8", 21),
        Pack("ganji_adabi", "گنجی ادبی – مرد (آفلاین)", "vits-piper-fa_IR-ganji_adabi-medium-int8", 20),
        Pack("mana", "مانا / مونا – زن (آفلاین، ~۶۴ مگ)", "mana-hf", 64),
        Pack("musa", "موسی – مرد آفلاین (معادل فرید)", "vits-piper-fa_IR-amir-medium-int8", 21),
        Pack("khadijah", "خدیجه – زن آفلاین (معادل دلارا)", "vits-piper-fa_IR-ganji-medium-int8", 21),
    )''',
    vt,
    count=1,
)
if 'Pack("gyro"' in vt2:
    i = vt2.find('val PACKS = listOf')
    j = vt2.find('fun dir(', i)
    if i >= 0 and j > i:
        vt2 = vt2[:i] + '''val PACKS = listOf(
        Pack("amir", "امیر – مرد (آفلاین Piper)", "vits-piper-fa_IR-amir-medium-int8", 21),
        Pack("reza", "رضا – مرد (آفلاین Piper)", "vits-piper-fa_IR-reza_ibrahim-medium-int8", 21),
        Pack("ganji", "گنجی – مرد (آفلاین Piper)", "vits-piper-fa_IR-ganji-medium-int8", 21),
        Pack("ganji_adabi", "گنجی ادبی – مرد (آفلاین)", "vits-piper-fa_IR-ganji_adabi-medium-int8", 20),
        Pack("mana", "مانا / مونا – زن (آفلاین، ~۶۴ مگ)", "mana-hf", 64),
        Pack("musa", "موسی – مرد آفلاین (معادل فرید)", "vits-piper-fa_IR-amir-medium-int8", 21),
        Pack("khadijah", "خدیجه – زن آفلاین (معادل دلارا)", "vits-piper-fa_IR-ganji-medium-int8", 21),
    )

    ''' + vt2[j:]
vp.write_text(vt2, encoding='utf-8')
print('PACKS fixed, gyro gone:', 'gyro' not in Path(vp).read_text())

sa = src / 'SettingsActivity.kt'
sat = sa.read_text(encoding='utf-8')
if 'private fun bindExtraSettingsV54()\n        bindUnifiedApiV58()' in sat or 'bindExtraSettingsV54()\n        bindUnifiedApiV58() {' in sat:
    m = re.search(r'private fun bindExtraSettingsV54\(\)', sat)
    if m:
        sat = sat[:m.start()].rstrip() + '\n\n'

if 'bindUnifiedApiV58()' not in sat.split('private fun')[0]:
    if 'bindExtraSettingsV54()' not in sat:
        sat = sat.replace(
            'findViewById<Button>(R.id.btn_test)',
            'bindExtraSettingsV54()\n        bindUnifiedApiV58()\n        findViewById<Button>(R.id.btn_test)'
        )

methods = r'''
    private fun refreshVoiceSpinner() {
        try { /* optional spinner refresh */ } catch (_: Throwable) {}
    }

    private fun bindExtraSettingsV54() {
        try {
            val p = prefs
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
            findViewById<SwitchCompat>(R.id.sw_read_all_apps)?.let { sw ->
                sw.isChecked = try { p.readAllApps } catch (_: Throwable) { true }
                sw.setOnCheckedChangeListener { _, c ->
                    try { p.readAllApps = c } catch (_: Throwable) {}
                    findViewById<View>(R.id.btn_pick_apps)?.isEnabled = !c
                }
                findViewById<View>(R.id.btn_pick_apps)?.isEnabled = !sw.isChecked
            }
            findViewById<Button>(R.id.btn_pick_apps)?.setOnClickListener {
                try { showAppPicker() } catch (_: Throwable) {}
            }
        } catch (e: Exception) {
            android.util.Log.e("Settings", "bindExtraSettingsV54", e)
        }
    }

    private fun bindUnifiedApiV58() {
        try {
            val p = prefs
            findViewById<android.widget.EditText>(R.id.et_unified_api_key)?.apply {
                setText(p.unifiedApiKey.ifBlank {
                    listOf(p.azureKey, p.openAiApiKey, p.openRouterApiKey, p.googleApiKey, p.deepseekApiKey, p.grokApiKey, p.customApiKey)
                        .firstOrNull { it.isNotBlank() } ?: ""
                })
            }
            findViewById<android.widget.EditText>(R.id.et_custom_base_url)?.setText(p.customApiBaseUrl)
            findViewById<android.widget.TextView>(R.id.tv_api_status)?.text =
                if (p.detectedProvider.isNotBlank())
                    "پلتفرم: ${p.detectedProvider}" + if (p.apiIsPaid) " (پولی/پرو)" else " (رایگان)"
                else ""
            findViewById<SwitchCompat>(R.id.sw_page_turn_sound)?.apply {
                isChecked = p.pageTurnSound
                setOnCheckedChangeListener { _, c -> p.pageTurnSound = c }
            }
            findViewById<Button>(R.id.btn_detect_test_key)?.setOnClickListener {
                val key = findViewById<android.widget.EditText>(R.id.et_unified_api_key)?.text?.toString()?.trim() ?: ""
                val base = findViewById<android.widget.EditText>(R.id.et_custom_base_url)?.text?.toString()?.trim() ?: ""
                if (key.isBlank()) { toast("کلید را وارد کنید"); return@setOnClickListener }
                p.unifiedApiKey = key
                if (base.isNotBlank()) p.customApiBaseUrl = base
                findViewById<android.widget.TextView>(R.id.tv_api_status)?.text = "در حال تشخیص و تست…"
                Thread {
                    val r = MultiTts.detectAndTest(key, base)
                    runOnUiThread {
                        if (r.ok) {
                            MultiTts.applyDetectToPrefs(p, r)
                            findViewById<android.widget.TextView>(R.id.tv_api_status)?.text =
                                r.message + "\nصداها به فهرست اضافه شد."
                            toast("کلید معتبر – ${r.label}")
                            refreshVoiceSpinner()
                        } else {
                            findViewById<android.widget.TextView>(R.id.tv_api_status)?.text = r.message
                            toast("کلید کار نکرد")
                        }
                    }
                }.start()
            }
        } catch (e: Exception) {
            android.util.Log.e("Settings", "bindUnifiedApiV58", e)
        }
    }

}
'''

if not sat.rstrip().endswith('}'):
    sat = sat.rstrip() + '\n' + methods
else:
    sat = sat.rstrip()
    if sat.endswith('}'):
        sat = sat[:-1].rstrip() + '\n' + methods

if 'bindExtraSettingsV54()' not in sat[:sat.find('private fun bindExtraSettingsV54')]:
    for anchor in ['findViewById<Button>(R.id.btn_test)', 'findViewById<Button>(R.id.btn_reset)', 'sw_scene']:
        if anchor in sat:
            sat = sat.replace(anchor, 'bindExtraSettingsV54()\n        bindUnifiedApiV58()\n        ' + anchor, 1)
            break

if sat.count('private fun bindUnifiedApiV58') > 1:
    first = sat.find('private fun bindExtraSettingsV54')
    if first > 0:
        sat = sat[:first].rstrip() + '\n' + methods

sa.write_text(sat, encoding='utf-8')
print('SettingsActivity fixed')

bg = proj / 'app/build.gradle.kts'
bt = bg.read_text(encoding='utf-8')
if '5.8' not in bt:
    bt = bt.replace('versionCode = 57', 'versionCode = 58')
    bt = bt.replace('versionName = "5.7"', 'versionName = "5.8"')
    bg.write_text(bt, encoding='utf-8')
print('v5.8b DONE')
text = sa.read_text(encoding='utf-8')
if text.count('{') > text.count('}'):
    sa.write_text(text.rstrip() + '\n}\n', encoding='utf-8')
    text = sa.read_text(encoding='utf-8')
    print('fixed Settings braces')
print('open braces', text.count('{'), 'close', text.count('}'))
print('gyro in VoicePacks', 'gyro' in vp.read_text(encoding='='utf-8'))
print('bindUnified count', text.count('private fun bindUnifiedApiV58'))
print('bindExtra count', text.count('private fun bindExtraSettingsV54'))
print('FINAL v5.8b OK')
