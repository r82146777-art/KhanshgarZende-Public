#!/usr/bin/env python3
"""v5.8fix after v58all: fix compile errors."""
from pathlib import Path
import os, re, subprocess, sys

root = Path(__file__).resolve().parent
r = subprocess.run([sys.executable, str(root / 'patch_v58all.py')], check=False)
print('v58all', r.returncode)

proj = Path(os.environ['PROJ'])
src = proj / 'app/src/main/java/com/example/khanshgarzende'

# Prefs missing fields
prefs = src / 'Prefs.kt'
pt = prefs.read_text(encoding='utf-8')
need = []
if 'autoCleanText' not in pt:
    need.append('''
    var autoCleanText: Boolean
        get() = sp.getBoolean("auto_clean_text", true)
        set(v) = sp.edit().putBoolean("auto_clean_text", v).apply()
''')
if 'isPackageAllowed' not in pt:
    need.append('''
    fun isPackageAllowed(pkg: String): Boolean {
        if (readAllApps) return true
        val allowed = allowedPackages.split(',', '\\n').map { it.trim() }.filter { it.isNotEmpty() }
        if (allowed.isEmpty()) return true
        return pkg in allowed
    }
''')
if 'voiceGuide' not in pt:
    need.append('''
    var voiceGuide: Boolean
        get() = sp.getBoolean("voice_guide", true)
        set(v) = sp.edit().putBoolean("voice_guide", v).apply()
    var photoByButtonOnly: Boolean
        get() = sp.getBoolean("photo_by_button", true)
        set(v) = sp.edit().putBoolean("photo_by_button", v).apply()
    var autoPhoto: Boolean
        get() = sp.getBoolean("auto_photo", false)
        set(v) = sp.edit().putBoolean("auto_photo", v).apply()
    var autoPhotoSeconds: Int
        get() = sp.getInt("auto_photo_sec", 10)
        set(v) = sp.edit().putInt("auto_photo_sec", v).apply()
    var readAllApps: Boolean
        get() = sp.getBoolean("read_all_apps", true)
        set(v) = sp.edit().putBoolean("read_all_apps", v).apply()
    var allowedPackages: String
        get() = sp.getString("allowed_packages", "") ?: ""
        set(v) = sp.edit().putString("allowed_packages", v).apply()
''')
if need:
    pt = prefs.read_text(encoding='utf-8')
    # insert before final }
    idx = pt.rfind('}')
    prefs.write_text(pt[:idx] + ''.join(need) + '\n' + pt[idx:], encoding='utf-8')
    print('Prefs fields fixed')

# MultiTts compat: providers + synthPcm
mt = src / 'MultiTts.kt'
mtxt = mt.read_text(encoding='utf-8')
if 'fun providers' not in mtxt:
    compat = '''
    data class Provider(val id: String, val label: String, val baseUrl: String, val key: String)
    fun providers(p: Prefs): List<Provider> {
        val list = ArrayList<Provider>()
        val k = keyFor(p)
        val prov = activeProvider(p) ?: return list
        if (k.isNotBlank()) list.add(Provider(prov, prov, baseFor(prov, p.customApiBaseUrl), k))
        return list
    }
    fun synthPcm(p: Prefs, text: String, voice: String = "nova"): ShortArray? {
        val mp3 = synthMp3(p, text, voice) ?: return null
        // crude: not decoding mp3 here; caller may fall back
        return null
    }
'''
    idx = mtxt.rfind('}')
    mt.write_text(mtxt[:idx] + compat + '\n' + mtxt[idx:], encoding='utf-8')
    print('MultiTts compat')

# SettingsActivity: rewrite bind methods cleanly
sa = src / 'SettingsActivity.kt'
sat = sa.read_text(encoding='utf-8')
# Find broken bindExtraSettingsV54 without body
if re.search(r'private fun bindExtraSettingsV54\(\)\s*\n\s*bindUnifiedApiV58', sat) or 'Function' == 'x':
    # Remove from first bindExtraSettingsV54 to end of class and rewrite
    m = re.search(r'\n\s*private fun bindExtraSettingsV54\(\)', sat)
    if not m:
        m = re.search(r'\n\s*private fun bindUnifiedApiV58\(\)', sat)
    if m:
        head = sat[:m.start()]
        # ensure onCreate calls
        if 'bindUnifiedApiV58()' not in head:
            if 'bindExtraSettingsV54()' in head:
                head = head.replace('bindExtraSettingsV54()', 'bindExtraSettingsV54()\n        bindUnifiedApiV58()')
            else:
                head = head.replace(
                    'findViewById<Button>(R.id.btn_test)',
                    'bindExtraSettingsV54()\n        bindUnifiedApiV58()\n        findViewById<Button>(R.id.btn_test)',
                    1,
                )
        tail = '''

    private fun bindExtraSettingsV54() {
        try {
            val p = prefs
            findViewById<Button>(R.id.btn_accessibility)?.setOnClickListener {
                try { startActivity(android.content.Intent(android.provider.Settings.ACTION_ACCESSIBILITY_SETTINGS)) }
                catch (_: Exception) { toast("باز کردن دسترس‌پذیری ممکن نشد") }
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
                sw.setOnCheckedChangeListener { _, c -> try { p.readAllApps = c } catch (_: Throwable) {} }
            }
        } catch (e: Exception) { android.util.Log.e("Settings", "bindExtra", e) }
    }

    private fun bindUnifiedApiV58() {
        try {
            val p = prefs
            findViewById<android.widget.EditText>(R.id.et_unified_api_key)?.setText(
                p.unifiedApiKey.ifBlank {
                    listOf(p.azureKey, p.openAiApiKey, p.openRouterApiKey).firstOrNull { it.isNotBlank() } ?: ""
                }
            )
            findViewById<androidx.appcompat.widget.SwitchCompat>(R.id.sw_page_turn_sound)?.apply {
                isChecked = try { p.pageTurnSound } catch (_: Throwable) { true }
                setOnCheckedChangeListener { _, c -> try { p.pageTurnSound = c } catch (_: Throwable) {} }
            }
            findViewById<android.widget.Button>(R.id.btn_detect_test_key)?.setOnClickListener {
                val key = findViewById<android.widget.EditText>(R.id.et_unified_api_key)?.text?.toString()?.trim() ?: ""
                val base = findViewById<android.widget.EditText>(R.id.et_custom_base_url)?.text?.toString()?.trim() ?: ""
                if (key.isBlank()) { toast("کلید را وارد کنید"); return@setOnClickListener }
                p.unifiedApiKey = key
                if (base.isNotBlank()) p.customApiBaseUrl = base
                findViewById<android.widget.TextView>(R.id.tv_api_status)?.text = "در حال تست…"
                Thread {
                    val result = MultiTts.detectAndTest(key, base)
                    runOnUiThread {
                        if (result.ok) {
                            MultiTts.applyDetectToPrefs(p, result)
                            findViewById<android.widget.TextView>(R.id.tv_api_status)?.text = result.message
                            toast("کلید معتبر – ${result.label}")
                        } else {
                            findViewById<android.widget.TextView>(R.id.tv_api_status)?.text = result.message
                            toast("کلید کار نکرد")
                        }
                    }
                }.start()
            }
        } catch (e: Exception) { android.util.Log.e("Settings", "bindUnified", e) }
    }
}
'''
        sa.write_text(head.rstrip() + tail, encoding='utf-8')
        print('Settings rewritten')
    else:
        print('Settings pattern not found, leave')
else:
    print('Settings ok?')

# balance braces Settings
sat = sa.read_text(encoding='utf-8')
o, c = sat.count('{'), sat.count('}')
if o > c:
    sa.write_text(sat.rstrip() + '\n' + ('}' * (o - c)) + '\n', encoding='utf-8')
    print('braces fixed', o, c)

print('v5.8fix DONE')
