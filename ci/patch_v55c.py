#!/usr/bin/env python3
"""v5.5c: repair SettingsActivity if bindExtraSettingsV54 body was broken."""
from pathlib import Path
import os
import re

proj = Path(os.environ['PROJ'])
src = proj / 'app/src/main/java/com/example/khanshgarzende'
sa = src / 'SettingsActivity.kt'
if not sa.exists():
    raise SystemExit('no SettingsActivity')

st = sa.read_text(encoding='utf-8')

# Remove broken/duplicated bind methods from first occurrence of bindExtraSettingsV54 definition to end of class
# Keep class structure: cut at 'private fun bindExtraSettingsV54' or 'private fun bindAccessibilityAndApiV55'
m = re.search(r'\n    private fun bindExtraSettingsV5[34]\b', st)
m2 = re.search(r'\n    private fun bindAccessibilityAndApiV55\b', st)
cut = None
if m and m2:
    cut = min(m.start(), m2.start())
elif m:
    cut = m.start()
elif m2:
    cut = m2.start()

if cut is not None:
    head = st[:cut]
    # ensure head ends properly (not mid-function)
    # remove trailing incomplete bind call lines that are alone
    head = re.sub(r'\n\s*bindExtraSettingsV5[34]\(\)\s*\n\s*bindAccessibilityAndApiV55\(\)\s*\n\s*updateBoxes\(\)', '\n        bindExtraSettingsV54()\n        bindAccessibilityAndApiV55()\n        updateBoxes()', head)
    if 'bindExtraSettingsV54()' not in head and 'updateBoxes()' in head:
        head = head.replace('updateBoxes()', 'bindExtraSettingsV54()\n        bindAccessibilityAndApiV55()\n        updateBoxes()', 1)
    elif 'bindAccessibilityAndApiV55()' not in head and 'bindExtraSettingsV54()' in head:
        head = head.replace('bindExtraSettingsV54()', 'bindExtraSettingsV54()\n        bindAccessibilityAndApiV55()', 1)

    methods = '''

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
}
'''
    # Ensure EditText import
    if 'import android.widget.EditText' not in head:
        head = head.replace('import android.widget.Button', 'import android.widget.Button\nimport android.widget.EditText')
    sa.write_text(head.rstrip() + '\n' + methods, encoding='utf-8')
    print('SettingsActivity repaired')
else:
    print('no bind methods to repair; leave as-is')

print('v5.5c done')
