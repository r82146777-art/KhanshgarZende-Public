#!/usr/bin/env python3
"""v6.4b: hang fix + AQAb Gemini without breaking Settings syntax."""
from pathlib import Path
import os, re, subprocess, sys

root = Path(__file__).resolve().parent
# Run through v62 chain first (includes v61b + mini features)
print("v62", subprocess.run([sys.executable, str(root / "patch_v62.py")], check=False).returncode)

proj = Path(os.environ["PROJ"])
src = proj / "app/src/main/java/com/example/khanshgarzende"

# ---- MultiTts: replace detectAndTest + tg for AQAb ----
mt = src / "MultiTts.kt"
t = mt.read_text(encoding="utf-8")

if "fun detectAndTest" in t:
    t = re.sub(
        r'fun detectAndTest\(key:String, customBase:String=""\):DetectResult\{[\s\S]*?\n    \}\n    fun applyDetectToPrefs',
        '''fun detectAndTest(key:String, customBase:String=""):DetectResult{
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
    fun applyDetectToPrefs''',
        t,
        count=1,
    )

if "private fun tg(" in t:
    t = re.sub(
        r'private fun tg\(key:String\):Pair<Boolean,String>\{[\s\S]*?\n    \}\n    private fun to',
        '''private fun tg(key:String):Pair<Boolean,String>{
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
    private fun to''',
        t,
        count=1,
    )

mt.write_text(t, encoding="utf-8")
print("MultiTts OK")

# ---- Settings: fix empty bindMultiApiKeys + safe showAppPicker ----
sa = src / "SettingsActivity.kt"
sat = sa.read_text(encoding="utf-8")

# Close broken empty function if opened without body
sat = sat.replace(
    "private fun bindMultiApiKeysV56() {\n\n    private fun showAppPicker",
    "private fun bindMultiApiKeysV56() {}\n\n    private fun showAppPicker",
)
sat = sat.replace(
    "private fun bindMultiApiKeysV56() {\n    private fun showAppPicker",
    "private fun bindMultiApiKeysV56() {}\n    private fun showAppPicker",
)

# Remove any existing showAppPicker and append a clean one
sat = re.sub(r'\n    private fun showAppPicker\(\)[\s\S]*$', '\n', sat)
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
                    pm.getInstalledApplications(0)
                        .filter { pm.getLaunchIntentForPackage(it.packageName) != null }
                        .sortedBy { it.loadLabel(pm).toString() }
                } catch (_: Throwable) {
                    emptyList()
                }
                val labels = apps.map { it.loadLabel(pm).toString() + "\\n" + it.packageName }.toTypedArray()
                val allowed = p.allowedPackages.split(',', '\\n').map { it.trim() }.filter { it.isNotEmpty() }.toSet()
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
# Fix double-escaped newlines in Kotlin source - we want real \n in Kotlin strings for package split
picker = picker.replace('"\\n"', '"\n"')
picker = picker.replace("', '\\n'", "', '\n'")

sat = sat + "\n" + picker
sa.write_text(sat, encoding="utf-8")
print("Settings braces", sat.count('{'), sat.count('}'))

# SpeechManager safe reload
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
        st,
        count=1,
    )
sm.write_text(st, encoding="utf-8")

# version
bg = proj / "app/build.gradle.kts"
bt = bg.read_text(encoding="utf-8")
bt = re.sub(r"versionCode\s*=\s*\d+", "versionCode = 64", bt)
bt = re.sub(r'versionName\s*=\s*"[^"]*"', 'versionName = "6.4"', bt)
bg.write_text(bt, encoding="utf-8")
print("ALL v6.4b DONE")
