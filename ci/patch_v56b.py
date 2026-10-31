#!/usr/bin/env python3
"""v5.6b: repair SettingsActivity and SpeechManager companion prefs."""
from pathlib import Path
import os
import re

proj = Path(os.environ['PROJ'])
src = proj / 'app/src/main/java/com/example/khanshgarzende'

# ---- SpeechManager: companion voiceOptions uses Prefs(ctx) not prefs ----
sm = src / 'SpeechManager.kt'
t = sm.read_text(encoding='utf-8')
if 'MultiTts.providers(prefs)' in t:
    t = t.replace('MultiTts.providers(prefs)', 'MultiTts.providers(Prefs(ctx))')
    sm.write_text(t, encoding='utf-8')
    print('SpeechManager Prefs(ctx)')

# ---- SettingsActivity: rewrite tail methods cleanly ----
sa = src / 'SettingsActivity.kt'
st = sa.read_text(encoding='utf-8')

# Cut from first broken bind* method definition
m = re.search(r'\n    private fun bind(ExtraSettingsV5[34]|AccessibilityAndApiV55|MultiApiKeysV56)\b', st)
# simpler: cut at any of these definitions
cut_candidates = []
for pat in (r'\n    private fun bindExtraSettingsV54\b',
            r'\n    private fun bindAccessibilityAndApiV55\b',
            r'\n    private fun bindMultiApiKeysV56\b',
            r'\n    private fun showAppPicker\b'):
    m = re.search(pat, st)
    if m:
        cut_candidates.append(m.start())

if cut_candidates:
    cut = min(cut_candidates)
    head = st[:cut]
    # ensure calls in onCreate
    if 'bindMultiApiKeysV56()' not in head:
        if 'bindExtraSettingsV54()' in head:
            head = head.replace('bindExtraSettingsV54()', 'bindExtraSettingsV54()\n        bindAccessibilityAndApiV55()\n        bindMultiApiKeysV56()', 1)
        elif 'updateBoxes()' in head:
            head = head.replace('updateBoxes()', 'bindExtraSettingsV54()\n        bindAccessibilityAndApiV55()\n        bindMultiApiKeysV56()\n        updateBoxes()', 1)
    # clean duplicate calls
    head = re.sub(r'(bindExtraSettingsV54\(\)\s*)+', 'bindExtraSettingsV54()\n        ', head)
    head = re.sub(r'(bindAccessibilityAndApiV55\(\)\s*)+', 'bindAccessibilityAndApiV55()\n        ', head)
    head = re.sub(r'(bindMultiApiKeysV56\(\)\s*)+', 'bindMultiApiKeysV56()\n        ', head)

    methods = r'''

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

    private fun bindAccessibilityAndApiV55() {
        try {
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
            val selected = try {
                p.allowedPackages.split(',').map { it.trim() }.filter { it.isNotEmpty() }.toMutableSet()
            } catch (_: Throwable) { mutableSetOf() }
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

    private fun bindMultiApiKeysV56() {
        try {
            fun box(id: Int, get: () -> String, set: (String) -> Unit) {
                val e = findViewById<EditText>(id) ?: return
                e.setText(get())
                e.setOnFocusChangeListener { _, has -> if (!has) set(e.text?.toString()?.trim().orEmpty()) }
            }
            box(R.id.et_azure_key2, { p.azureKey }, { p.azureKey = it })
            box(R.id.et_azure_region2, { p.azureRegion }, { p.azureRegion = it.ifBlank { "westeurope" } })
            box(R.id.et_openai_key, { p.openAiApiKey }, { p.openAiApiKey = it })
            box(R.id.et_openrouter_key, { p.openRouterApiKey }, { p.openRouterApiKey = it })
            box(R.id.et_google_key, { p.googleApiKey }, { p.googleApiKey = it })
            box(R.id.et_deepseek_key, { p.deepseekApiKey }, { p.deepseekApiKey = it })
            box(R.id.et_grok_key, { p.grokApiKey }, { p.grokApiKey = it })
            box(R.id.et_custom_key, { p.customApiKey }, { p.customApiKey = it })
            box(R.id.et_custom_base, { p.customApiBaseUrl }, { p.customApiBaseUrl = it })
            val labels = arrayOf("Azure", "OpenAI", "OpenRouter", "DeepSeek", "Grok", "سفارشی")
            val ids = arrayOf("azure", "openai", "openrouter", "deepseek", "grok", "custom")
            val sp = findViewById<android.widget.Spinner>(R.id.sp_online_provider)
            if (sp != null) {
                sp.adapter = android.widget.ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, labels)
                val cur = ids.indexOf(p.onlineProvider).let { if (it < 0) 0 else it }
                sp.setSelection(cur)
                sp.onItemSelectedListener = object : android.widget.AdapterView.OnItemSelectedListener {
                    override fun onItemSelected(parent: android.widget.AdapterView<*>?, view: android.view.View?, position: Int, id: Long) {
                        p.onlineProvider = ids[position]
                    }
                    override fun onNothingSelected(parent: android.widget.AdapterView<*>?) {}
                }
            }
        } catch (e: Throwable) {
            android.util.Log.e("Settings", "bindMultiApiKeysV56", e)
        }
    }
}
'''
    if 'import android.widget.EditText' not in head:
        head = head.replace('import android.widget.Button', 'import android.widget.Button\nimport android.widget.EditText')
    sa.write_text(head.rstrip() + '\n' + methods, encoding='utf-8')
    print('SettingsActivity fully repaired')
else:
    print('no cut point; leave Settings')

print('v5.6b done')
