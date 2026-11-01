#!/usr/bin/env python3
"""v6.2 mini part A: Gemini detect + safe isOnline"""
from pathlib import Path
import os, re, subprocess, sys
root = Path(__file__).resolve().parent
print("v61b", subprocess.run([sys.executable, str(root/"patch_v61b.py")], check=False).returncode)
proj = Path(os.environ["PROJ"])
src = proj/"app/src/main/java/com/example/khanshgarzende"
res = proj/"app/src/main/res"

# MultiTts detect
mt = src/"MultiTts.kt"
t = mt.read_text(encoding="utf-8")
if "fun detectAndTest" not in t:
    t = t.replace(
        'if (p.customApiKey.isNotBlank() && p.customApiBaseUrl.isNotBlank())',
        'if (p.googleApiKey.isNotBlank()) list.add(Provider("google","Google/Gemini","https://generativelanguage.googleapis.com/v1beta",p.googleApiKey))\n'
        '        if (p.unifiedApiKey.isNotBlank() && p.detectedProvider in listOf("google","gemini")) '
        'list.add(Provider("google","Google/Gemini","https://generativelanguage.googleapis.com/v1beta",p.unifiedApiKey))\n'
        '        if (p.unifiedApiKey.isNotBlank() && p.detectedProvider=="openai" && list.none{it.id=="openai"}) '
        'list.add(Provider("openai","OpenAI","https://api.openai.com/v1",p.unifiedApiKey))\n'
        '        if (p.customApiKey.isNotBlank() && p.customApiBaseUrl.isNotBlank())'
    )
    t = t[:t.rfind("}")] + r'''
    data class DetectResult(val ok:Boolean,val providerId:String,val label:String,val message:String,val isPaid:Boolean=false,val voicesCsv:String="",val baseUrl:String="")
    fun detectAndTest(key:String, customBase:String=""):DetectResult{
        val k=key.trim(); if(k.isBlank()) return DetectResult(false,"","","empty")
        val base=customBase.trim().trimEnd('/')
        val tries=ArrayList<Triple<String,String,String>>()
        if(base.isNotBlank()) tries.add(Triple("custom","custom",base))
        if(k.startsWith("AIza")) tries.add(Triple("google","Google/Gemini","gemini"))
        if(k.startsWith("sk-or-")) tries.add(Triple("openrouter","OpenRouter","https://openrouter.ai/api/v1"))
        if(k.startsWith("xai-")) tries.add(Triple("grok","Grok","https://api.x.ai/v1"))
        if(k.startsWith("sk-")) tries.add(Triple("openai","OpenAI","https://api.openai.com/v1"))
        tries.add(Triple("google","Google/Gemini","gemini"))
        tries.add(Triple("openrouter","OpenRouter","https://openrouter.ai/api/v1"))
        tries.add(Triple("openai","OpenAI","https://api.openai.com/v1"))
        tries.add(Triple("deepseek","DeepSeek","https://api.deepseek.com/v1"))
        tries.add(Triple("grok","Grok","https://api.x.ai/v1"))
        var last="fail"; val seen=HashSet<String>()
        for((id,label,b) in tries){ val sk=id+b; if(sk in seen) continue; seen.add(sk)
            try{ val (ok,msg)=if(b=="gemini"||id=="google") tg(k) else to(b,k)
                if(ok) return DetectResult(true,id,label,"OK $label: $msg",false,"",if(b=="gemini")"" else b)
                last="$label: $msg"
            }catch(e:Throwable){ last="$label: ${e.message}" } }
        return DetectResult(false,"","",last)
    }
    fun applyDetectToPrefs(p:Prefs,r:DetectResult){
        if(!r.ok) return; p.detectedProvider=r.providerId; p.onlineProvider=r.providerId; p.apiIsPaid=r.isPaid
        val key=p.unifiedApiKey
        when(r.providerId){
            "openai"->p.openAiApiKey=key; "openrouter"->p.openRouterApiKey=key
            "deepseek"->p.deepseekApiKey=key; "grok"->p.grokApiKey=key
            "google","gemini"->p.googleApiKey=key
            "custom"->{ p.customApiKey=key; if(r.baseUrl.isNotBlank()) p.customApiBaseUrl=r.baseUrl }
        }
    }
    private fun tg(key:String):Pair<Boolean,String>{
        val url=URL("https://generativelanguage.googleapis.com/v1beta/models?key="+java.net.URLEncoder.encode(key,"UTF-8"))
        val c=(url.openConnection() as HttpURLConnection).apply{requestMethod="GET";connectTimeout=12000;readTimeout=15000}
        return try{ val code=c.responseCode; if(code in 200..299) Pair(true,"Gemini OK") else Pair(false,"HTTP $code") } finally{c.disconnect()}
    }
    private fun to(baseUrl:String,key:String):Pair<Boolean,String>{
        try{ val url=URL(baseUrl.trimEnd('/')+"/models")
            val c=(url.openConnection() as HttpURLConnection).apply{requestMethod="GET";connectTimeout=10000;readTimeout=12000;setRequestProperty("Authorization","Bearer $key")}
            try{ val code=c.responseCode; if(code in 200..299) return Pair(true,"OK"); if(code==401||code==403) return Pair(false,"rej $code") } finally{c.disconnect()}
        }catch(_:Throwable){}
        return try{ val url=URL(baseUrl.trimEnd('/')+"/chat/completions")
            val model=when{ baseUrl.contains("deepseek")-> "deepseek-chat"; baseUrl.contains("openrouter")-> "openai/gpt-4o-mini"; baseUrl.contains("x.ai")-> "grok-2-latest"; else->"gpt-4o-mini"}
            val body=JSONObject().put("model",model).put("max_tokens",5).put("messages",JSONArray().put(JSONObject().put("role","user").put("content","hi"))).toString()
            val c=(url.openConnection() as HttpURLConnection).apply{requestMethod="POST";connectTimeout=12000;readTimeout=20000;doOutput=true;setRequestProperty("Content-Type","application/json");setRequestProperty("Authorization","Bearer $key")}
            try{ c.outputStream.use{it.write(body.toByteArray(Charsets.UTF_8))}; if(c.responseCode in 200..299) Pair(true,"chat") else Pair(false,"HTTP ${c.responseCode}") } finally{c.disconnect()}
        }catch(e:Throwable){ Pair(false,e.message?:"err") }
    }
}
'''
    mt.write_text(t, encoding="utf-8"); print("MultiTts")

# SpeechManager: only isOnline fix (safe)
sm=src/"SpeechManager.kt"; st=sm.read_text(encoding="utf-8")
st=st.replace(
    'private val isOnline get() = prefs.voice == "dilara" || prefs.voice == "farid" || prefs.voice.startsWith("api:")',
    'private val isOnline get() = prefs.voice.startsWith("api:")',
)
sm.write_text(st,encoding="utf-8"); print("SM")
