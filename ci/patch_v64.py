#!/usr/bin/env python3
"""v6.4: no hang — fast key detect for AQAb Gemini, bg app picker, short timeouts."""
from pathlib import Path
import os, re, subprocess, sys

root = Path(__file__).resolve().parent
print("v62", subprocess.run([sys.executable, str(root / "patch_v62.py")], check=False).returncode)

proj = Path(os.environ["PROJ"])
src = proj / "app/src/main/java/com/example/khanshgarzende"

# ── Rewrite detectAndTest block in MultiTts for fast AQAb + short timeouts ──
mt = src / "MultiTts.kt"
t = mt.read_text(encoding="utf-8")

# Replace entire detectAndTest function if present
new_detect = r'''
    fun detectAndTest(key:String, customBase:String=""):DetectResult{
        val k=key.trim(); if(k.isBlank()) return DetectResult(false,"","","empty")
        val base=customBase.trim().trimEnd('/')
        // Fast path: known prefixes — only try matching provider (no long cascade)
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
                // unknown: try gemini then openai only (2 attempts max)
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
        t,
        count=1,
    )
else:
    print("WARNING no detectAndTest")

# Replace tg() to use x-goog-api-key header + shorter timeout (critical for AQ. keys)
new_tg = r'''
    private fun tg(key:String):Pair<Boolean,String>{
        // New Gemini Auth keys (AQ./AQAb) work with ?key= or x-goog-api-key — NOT Bearer
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
        t,
        count=1,
    )

# Shorter timeouts on to()
# Also fix chatDescribe for Gemini AQ keys if present
if "private fun chatGemini" in t or "fun chatDescribe" in t:
    t = t.replace(
        'setRequestProperty("Authorization", "Bearer ${prov.key}")',
        'if (prov.id == "google") setRequestProperty("x-goog-api-key", prov.key) else setRequestProperty("Authorization", "Bearer ${prov.key}")',
    )

mt.write_text(t, encoding="utf-8")
print("MultiTts detect fast + AQAb")

# ── Settings: app picker on background thread; detect already on Thread ──
sa = src / "SettingsActivity.kt"
sat = sa.read_text(encoding="utf-8")

# Replace showAppPicker to not block UI
new_picker = r'''
    private fun showAppPicker(){
        val status = findViewById<android.widget.TextView?>(R.id.tv_api_status)
        status?.text = "در حال بارگذاری فهرست برنامه‌ها…"
        Thread {
            try{
                val pm=packageManager
                val apps=try{
                    pm.getInstalledApplications(0)
                        .filter{ pm.getLaunchIntentForPackage(it.packageName)!=null }
                        .sortedBy{ it.loadLabel(pm).toString() }
                }catch(_:Throwable){ emptyList() }
                val labels=apps.map{ it.loadLabel(pm).toString()+"\n"+it.packageName }.toTypedArray()
                val checked=BooleanArray(apps.size){ i ->
                    p.allowedPackages.split(',','\n').map{it.trim()}.filter{it.isNotEmpty()}.contains(apps[i].packageName)
                }
                runOnUiThread {
                    status?.text = ""
                    if(apps.isEmpty()){ toast("لیست برنامه‌ها در دسترس نیست"); return@runOnUiThread }
                    androidx.appcompat.app.AlertDialog.Builder(this)
                        .setTitle("برنامه‌ها")
                        .setMultiChoiceItems(labels, checked){ _, w, c -> checked[w]=c }
                        .setPositiveButton("ذخیره"){ _, _ ->
                            val sel=apps.indices.filter{checked[it]}.map{apps[it].packageName}
                            p.allowedPackages=sel.joinToString(",")
                            p.readAllApps=false
                            findViewById<androidx.appcompat.widget.SwitchCompat?>(R.id.sw_read_all_apps)?.isChecked=false
                            findViewById<View?>(R.id.btn_pick_apps)?.visibility=View.VISIBLE
                            toast("${sel.size} برنامه")
                        }
                        .setNegativeButton("انصراف", null)
                        .show()
                }
            }catch(e:Throwable){
                android.util.Log.e("S","pick",e)
                runOnUiThread{ status?.text=""; toast("خطا در بارگذاری برنامه‌ها") }
            }
        }.start()
    }
'''

if "fun showAppPicker" in sat:
    sat = re.sub(
        r'private fun showAppPicker\(\)\s*\{[\s\S]*?\n    \}\n\}',
        new_picker.strip() + "\n}\n",
        sat,
        count=1,
    )
else:
    idx = sat.rfind("}")
    sat = sat[:idx] + new_picker + "\n}\n"

# Harden onCreate: wrap spinner systemEngines in try (can be slow)
sat = sat.replace(
    'engines = listOf("" to "پیش‌فرض گوشی") + app.speech.systemEngines()',
    'engines = try { listOf("" to "پیش‌فرض گوشی") + app.speech.systemEngines() } catch (_: Throwable) { listOf("" to "پیش‌فرض گوشی") }',
)

# selectVoice: do NOT call reloadVoice on UI path in a way that blocks — already try/catch
# Make reloadVoice never block: ensure stop is quick
sa.write_text(sat, encoding="utf-8")
print("Settings no-hang picker")

# SpeechManager: safe stop + non-blocking reload
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
print("SpeechManager reload safe")

# version 6.4
bg = proj / "app/build.gradle.kts"
bt = bg.read_text(encoding="utf-8")
bt = re.sub(r"versionCode\s*=\s*\d+", "versionCode = 64", bt)
bt = re.sub(r'versionName\s*=\s*"[^"]*"', 'versionName = "6.4"', bt)
bg.write_text(bt, encoding="utf-8")
print("ALL v6.4 DONE")
