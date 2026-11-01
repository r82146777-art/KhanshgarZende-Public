#!/usr/bin/env python3
"""v6.5: no-hang Settings/app-picker + AQAb Gemini keys + safe voice switch."""
from pathlib import Path
import os, re, subprocess, sys

root = Path(__file__).resolve().parent
print("v62", subprocess.run([sys.executable, str(root / "patch_v62.py")], check=False).returncode)

proj = Path(os.environ["PROJ"])
src = proj / "app/src/main/java/com/example/khanshgarzende"

# ========== MultiTts: fast detect + AQAb + x-goog-api-key ==========
mt = src / "MultiTts.kt"
t = mt.read_text(encoding="utf-8")

new_detect = '''
    fun detectAndTest(key:String, customBase:String=""):DetectResult{
        val k=key.trim(); if(k.isBlank()) return DetectResult(false,"","","empty")
        val base=customBase.trim().trimEnd('/')
        val tries=ArrayList<Triple<String,String,String>>()
        if(base.isNotBlank()) tries.add(Triple("custom","custom",base))
        val isGemini = k.startsWith("AIza") || k.startsWith("AQAb") || k.startsWith("AQ.") || k.startsWith("AIzaSy") || (k.startsWith("AQ") && k.length>=20)
        val isOr = k.startsWith("sk-or-")
        val isXai = k.startsWith("xai-")
        val isSk = k.startsWith("sk-") && !isOr
        when {
            isGemini -> tries.add(Triple("google","Google/Gemini","gemini"))
            isOr -> tries.add(Triple("openrouter","OpenRouter","https://openrouter.ai/api/v1"))
            isXai -> tries.add(Triple("grok","Grok","https://api.x.ai/v1"))
            isSk -> {
                tries.add(Triple("openai","OpenAI","https://api.openai.com/v1"))
                tries.add(Triple("deepseek","DeepSeek","https://api.deepseek.com/v1"))
            }
            else -> {
                tries.add(Triple("google","Google/Gemini","gemini"))
                tries.add(Triple("openai","OpenAI","https://api.openai.com/v1"))
            }
        }
        var last="fail"; val seen=HashSet<String>()
        for((id,label,b) in tries){
            val sk=id+b; if(sk in seen) continue; seen.add(sk)
            try{
                val (ok,msg)=if(b=="gemini"||id=="google") tg(k) else to(b,k)
                if(ok) return DetectResult(true,id,label,"OK $label: $msg",false,"",if(b=="gemini")"" else b)
                last="$label: $msg"
            }catch(e:Throwable){ last="$label: ${e.message}" }
        }
        return DetectResult(false,"","",last)
    }
'''

if "fun detectAndTest" in t:
    t = re.sub(
        r'fun detectAndTest\(key:String, customBase:String=""\):DetectResult\{[\s\S]*?\n    \}\n    fun applyDetectToPrefs',
        new_detect.strip() + "\n    fun applyDetectToPrefs",
        t, count=1,
    )
else:
    t = t[:t.rfind("}")] + "\n" + new_detect + "\n}\n"

new_tg = '''
    private fun tg(key:String):Pair<Boolean,String>{
        val url=URL("https://generativelanguage.googleapis.com/v1beta/models?key="+java.net.URLEncoder.encode(key,"UTF-8"))
        val c=(url.openConnection() as HttpURLConnection).apply{
            requestMethod="GET"; connectTimeout=6000; readTimeout=8000
            setRequestProperty("x-goog-api-key", key)
        }
        return try{
            val code=c.responseCode
            val body=try{(if(code in 200..299)c.inputStream else c.errorStream)?.bufferedReader()?.readText()?:""}catch(_:Throwable){""}
            if(code in 200..299) Pair(true, if(body.contains("gemini",true)) "Gemini models OK" else "Google key OK")
            else Pair(false,"HTTP $code ${body.take(100)}")
        } finally{c.disconnect()}
    }
'''

if "private fun tg(" in t:
    t = re.sub(
        r'private fun tg\(key:String\):Pair<Boolean,String>\{[\s\S]*?\n    \}\n    private fun to',
        new_tg.strip() + "\n    private fun to",
        t, count=1,
    )
else:
    t = t[:t.rfind("}")] + "\n" + new_tg + "\n}\n"

mt.write_text(t, encoding="utf-8")
print("MultiTts AQAb+fast OK")

# ========== SettingsActivity: clean showAppPicker (NO broken newlines) ==========
sa = src / "SettingsActivity.kt"
sat = sa.read_text(encoding="utf-8")

if "import android.content.pm.PackageManager" not in sat:
    sat = sat.replace(
        "import android.content.Intent",
        "import android.content.Intent\nimport android.content.pm.PackageManager",
        1,
    )

sat = sat.replace(
    'private fun bindMultiApiKeysV56() {\n\n    private fun showAppPicker()',
    'private fun bindMultiApiKeysV56() {}\n\n    private fun showAppPicker()',
)
sat = sat.replace(
    'private fun bindMultiApiKeysV56() {\n    private fun showAppPicker()',
    'private fun bindMultiApiKeysV56() {}\n    private fun showAppPicker()',
)
if 'private fun bindMultiApiKeysV56() {' in sat and 'private fun bindMultiApiKeysV56() {}' not in sat:
    sat = sat.replace('private fun bindMultiApiKeysV56() {', 'private fun bindMultiApiKeysV56() {}', 1)

sat = re.sub(
    r'\n    private fun showAppPicker\(\)[\s\S]*?\n\}\s*$',
    '\n}\n',
    sat,
)
if 'private fun showAppPicker' in sat:
    sat = re.sub(r'\n    private fun showAppPicker\(\)[\s\S]*$', '\n}\n', sat)

sat = sat.rstrip()
if sat.endswith('}'):
    sat = sat[:-1].rstrip()

picker = '''
    private fun showAppPicker() {
        val status = findViewById<android.widget.TextView?>(R.id.tv_api_status)
        status?.text = "..."
        Thread {
            try {
                val pm = packageManager
                val apps = try {
                    @Suppress("DEPRECATION")
                    pm.getInstalledApplications(PackageManager.GET_META_DATA)
                        .filter { ai ->
                            try {
                                pm.getLaunchIntentForPackage(ai.packageName) != null &&
                                    ai.packageName != packageName
                            } catch (_: Throwable) { false }
                        }
                        .sortedBy { ai ->
                            try { ai.loadLabel(pm).toString() } catch (_: Throwable) { ai.packageName }
                        }
                } catch (_: Throwable) {
                    emptyList()
                }
                val labels = apps.map { ai ->
                    val name = try { ai.loadLabel(pm).toString() } catch (_: Throwable) { ai.packageName }
                    name + " | " + ai.packageName
                }.toTypedArray()
                val allowedSet = try {
                    p.allowedPackages.replace(10.toChar(), ',').replace(13.toChar(), ',')
                        .split(',').map { it.trim() }.filter { it.isNotEmpty() }.toSet()
                } catch (_: Throwable) {
                    emptySet<String>()
                }
                val checked = BooleanArray(apps.size) { i -> apps[i].packageName in allowedSet }
                runOnUiThread {
                    status?.text = ""
                    if (apps.isEmpty()) {
                        toast("0")
                        return@runOnUiThread
                    }
                    androidx.appcompat.app.AlertDialog.Builder(this@SettingsActivity)
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
                        .setOnDismissListener { status?.text = "" }
                        .show()
                }
            } catch (e: Throwable) {
                android.util.Log.e("Settings", "showAppPicker", e)
                runOnUiThread { status?.text = "" }
            }
        }.start()
    }
}
'''

sat = sat + "\n" + picker
sa.write_text(sat, encoding="utf-8")
print("Settings braces", sat.count("{"), sat.count("}"))

sm = src / "SpeechManager.kt"
st = sm.read_text(encoding="utf-8")
if "fun reloadVoice" in st:
    st = re.sub(
        r'fun reloadVoice\(\)\s*\{[\s\S]*?\n    \}',
        '''fun reloadVoice() {
        try { stop() } catch (_: Throwable) {}
        try { synchronized(cache) { cache.clear() } } catch (_: Throwable) {}
        Thread {
            try { warmUp() } catch (e: Throwable) { Log.e(TAG, "reloadVoice", e) }
        }.start()
    }''',
        st, count=1,
    )
st = st.replace(
    'private val isOnline get() = prefs.voice == "dilara" || prefs.voice == "farid" || prefs.voice.startsWith("api:")',
    'private val isOnline get() = prefs.voice.startsWith("api:")',
)
sm.write_text(st, encoding="utf-8")
print("SpeechManager OK")

bg = proj / "app/build.gradle.kts"
bt = bg.read_text(encoding="utf-8")
bt = re.sub(r"versionCode\s*=\s*\d+", "versionCode = 65", bt)
bt = re.sub(r'versionName\s*=\s*"[^"]*"', 'versionName = "6.5"', bt)
bg.write_text(bt, encoding="utf-8")
print("ALL v6.5 DONE")
