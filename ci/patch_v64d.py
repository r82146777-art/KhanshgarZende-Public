#!/usr/bin/env python3
from pathlib import Path
import os, re, subprocess, sys
root = Path(__file__).resolve().parent
print('v64c', subprocess.run([sys.executable, str(root/'patch_v64c.py')], check=False).returncode)
proj = Path(os.environ['PROJ'])
sa = proj/'app/src/main/java/com/example/khanshgarzende/SettingsActivity.kt'
t = sa.read_text(encoding='utf-8')
# Remove broken showAppPicker entirely
t = re.sub(r'\n    private fun showAppPicker\(\)[\s\S]*$', '\n', t)
t = t.rstrip()
if t.endswith('}'):
    t = t[:-1].rstrip()
# Append clean version — no \\n in Kotlin strings
picker = r'''
    private fun showAppPicker() {
        val status = findViewById<android.widget.TextView?>(R.id.tv_api_status)
        status?.text = "..."
        Thread {
            try {
                val pm = packageManager
                val apps = try {
                    pm.getInstalledApplications(0)
                        .filter { pm.getLaunchIntentForPackage(it.packageName) != null }
                        .sortedBy { it.loadLabel(pm).toString() }
                } catch (_: Throwable) {
                    emptyList()
                }
                val labels = apps.map { it.loadLabel(pm).toString() + " | " + it.packageName }.toTypedArray()
                val allowed = p.allowedPackages.split(Regex("[,\\n\\]")).map { it.trim() }.filter { it.isNotEmpty() }.toSet()
                val checked = BooleanArray(apps.size) { i -> apps[i].packageName in allowed }
                runOnUiThread {
                    status?.text = ""
                    if (apps.isEmpty()) {
                        toast("?")
                        return@runOnUiThread
                    }
                    androidx.appcompat.app.AlertDialog.Builder(this)
                        .setTitle("apps")
                        .setMultiChoiceItems(labels, checked) { _, which, isChecked ->
                            checked[which] = isChecked
                        }
                        .setPositiveButton("OK") { _, _ ->
                            val sel = apps.indices.filter { checked[it] }.map { apps[it].packageName }
                            p.allowedPackages = sel.joinToString(",")
                            p.readAllApps = false
                            findViewById<androidx.appcompat.widget.SwitchCompat?>(R.id.sw_read_all_apps)?.isChecked = false
                            findViewById<View?>(R.id.btn_pick_apps)?.visibility = View.VISIBLE
                            toast(sel.size.toString())
                        }
                        .setNegativeButton("X", null)
                        .show()
                }
            } catch (e: Throwable) {
                android.util.Log.e("S", "pick", e)
                runOnUiThread { status?.text = "" }
            }
        }.start()
    }
}
'''
# Fix regex: in Kotlin source we need Regex("[,\n\r]") which in a Python raw string is Regex("[,\n\r]")
# The r''' above has \\n which becomes \n in file = correct for Kotlin string of backslash-n? 
# We want Kotlin: Regex("[,\n\r]")  i.e. characters comma, newline, cr
# In the written file content: Regex("[,\n\r]")
picker = picker.replace('Regex("[,\\n\\]")', 'Regex("[,\\n\\r]")')
t = t + '\n' + picker
sa.write_text(t, encoding='utf-8')
print('Settings braces', t.count('{'), t.count('}'))
print('v64d DONE')
