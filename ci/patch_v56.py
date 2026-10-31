#!/usr/bin/env python3
"""v5.6: multi-platform API keys (Azure, Google, OpenAI, OpenRouter, DeepSeek, Grok, custom)."""
from pathlib import Path
import os
import subprocess
import sys

root = Path(__file__).resolve().parent
for name in ('patch_v54.py', 'patch_v54b.py', 'patch_v54c.py', 'patch_v55b.py', 'patch_v55c.py'):
    p = root / name
    if p.exists():
        r = subprocess.run([sys.executable, str(p)], check=False)
        print(name, 'exit', r.returncode)

proj = Path(os.environ['PROJ'])
src = proj / 'app/src/main/java/com/example/khanshgarzende'
res = proj / 'app/src/main/res'

prefs = src / 'Prefs.kt'
t = prefs.read_text(encoding='utf-8')
if 'openRouterApiKey' not in t:
    block = '''
    var openAiApiKey: String
        get() = sp.getString("openai_key", "") ?: ""
        set(v) = sp.edit().putString("openai_key", v.trim()).apply()
    var openRouterApiKey: String
        get() = sp.getString("openrouter_key", "") ?: ""
        set(v) = sp.edit().putString("openrouter_key", v.trim()).apply()
    var googleApiKey: String
        get() = sp.getString("google_key", "") ?: ""
        set(v) = sp.edit().putString("google_key", v.trim()).apply()
    var deepseekApiKey: String
        get() = sp.getString("deepseek_key", "") ?: ""
        set(v) = sp.edit().putString("deepseek_key", v.trim()).apply()
    var grokApiKey: String
        get() = sp.getString("grok_key", "") ?: ""
        set(v) = sp.edit().putString("grok_key", v.trim()).apply()
    var customApiKey: String
        get() = sp.getString("custom_key", "") ?: ""
        set(v) = sp.edit().putString("custom_key", v.trim()).apply()
    var customApiBaseUrl: String
        get() = sp.getString("custom_base", "") ?: ""
        set(v) = sp.edit().putString("custom_base", v.trim().trimEnd('/')).apply()
    var onlineProvider: String
        get() = sp.getString("online_provider", "azure") ?: "azure"
        set(v) = sp.edit().putString("online_provider", v).apply()
    var openaiTtsVoice: String
        get() = sp.getString("openai_tts_voice", "nova") ?: "nova"
        set(v) = sp.edit().putString("openai_tts_voice", v).apply()
'''
    idx = t.rfind('}')
    prefs.write_text(t[:idx] + block + '\n' + t[idx:], encoding='utf-8')
    print('Prefs multi keys')
else:
    print('Prefs ok')

(src / 'MultiTts.kt').write_text(r'''package com.example.khanshgarzende

import android.media.MediaCodec
import android.media.MediaExtractor
import android.media.MediaFormat
import android.util.Log
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.nio.ByteBuffer
import java.nio.ByteOrder

object MultiTts {
    private const val TAG = "MultiTts"

    data class Provider(val id: String, val label: String, val baseUrl: String, val key: String)

    fun providers(p: Prefs): List<Provider> {
        val list = ArrayList<Provider>()
        if (p.openAiApiKey.isNotBlank())
            list.add(Provider("openai", "OpenAI", "https://api.openai.com/v1", p.openAiApiKey))
        if (p.openRouterApiKey.isNotBlank())
            list.add(Provider("openrouter", "OpenRouter", "https://openrouter.ai/api/v1", p.openRouterApiKey))
        if (p.deepseekApiKey.isNotBlank())
            list.add(Provider("deepseek", "DeepSeek", "https://api.deepseek.com/v1", p.deepseekApiKey))
        if (p.grokApiKey.isNotBlank())
            list.add(Provider("grok", "Grok / xAI", "https://api.x.ai/v1", p.grokApiKey))
        if (p.customApiKey.isNotBlank() && p.customApiBaseUrl.isNotBlank())
            list.add(Provider("custom", "سفارشی", p.customApiBaseUrl, p.customApiKey))
        return list
    }

    fun activeProvider(p: Prefs): Provider? {
        val all = providers(p)
        if (all.isEmpty()) return null
        return all.firstOrNull { it.id == p.onlineProvider } ?: all.first()
    }

    fun synthPcm(p: Prefs, text: String): Pair<ShortArray, Int> {
        val mp3 = synthMp3(p, text)
        return decodeMp3ToPcm(mp3)
    }

    fun synthMp3(p: Prefs, text: String): ByteArray {
        val prov = activeProvider(p) ?: throw IllegalStateException("کلید API تنظیم نشده")
        val url = URL(prov.baseUrl.trimEnd('/') + "/audio/speech")
        val body = JSONObject()
            .put("model", "tts-1")
            .put("input", text.take(4000))
            .put("voice", p.openaiTtsVoice.ifBlank { "nova" })
            .put("response_format", "mp3")
            .toString()
        val c = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = 20000
            readTimeout = 60000
            doOutput = true
            setRequestProperty("Content-Type", "application/json")
            setRequestProperty("Authorization", "Bearer ${prov.key}")
            if (prov.id == "openrouter") {
                setRequestProperty("HTTP-Referer", "https://khanshgarzende.app")
                setRequestProperty("X-Title", "KhanshgarZende")
            }
        }
        try {
            c.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
            val code = c.responseCode
            if (code == 401 || code == 403) throw RuntimeException("کلید ${prov.label} نامعتبر است")
            if (code == 404) throw RuntimeException("${prov.label} از TTS پشتیبانی نمی‌کند")
            if (code !in 200..299) {
                val err = try { c.errorStream?.readBytes()?.toString(Charsets.UTF_8) } catch (_: Throwable) { null }
                Log.e(TAG, "TTS $code $err")
                throw RuntimeException("خطای ${prov.label} ($code)")
            }
            val out = ByteArrayOutputStream()
            c.inputStream.use { it.copyTo(out) }
            if (out.size() == 0) throw RuntimeException("صدایی دریافت نشد")
            return out.toByteArray()
        } finally {
            c.disconnect()
        }
    }

    fun decodeMp3ToPcm(mp3: ByteArray): Pair<ShortArray, Int> {
        val tmp = File.createTempFile("mt", ".mp3")
        try {
            tmp.writeBytes(mp3)
            val extractor = MediaExtractor()
            extractor.setDataSource(tmp.absolutePath)
            var track = -1
            var format: MediaFormat? = null
            for (i in 0 until extractor.trackCount) {
                val f = extractor.getTrackFormat(i)
                val mime = f.getString(MediaFormat.KEY_MIME) ?: continue
                if (mime.startsWith("audio/")) { track = i; format = f; break }
            }
            if (track < 0 || format == null) throw RuntimeException("فرمت صدا شناخته نشد")
            extractor.selectTrack(track)
            val mime = format.getString(MediaFormat.KEY_MIME)!!
            val sampleRate = format.getInteger(MediaFormat.KEY_SAMPLE_RATE)
            val codec = MediaCodec.createDecoderByType(mime)
            codec.configure(format, null, null, 0)
            codec.start()
            val info = MediaCodec.BufferInfo()
            val pcmOut = ArrayList<Short>(sampleRate * 4)
            var inputDone = false
            var outputDone = false
            while (!outputDone) {
                if (!inputDone) {
                    val inIdx = codec.dequeueInputBuffer(10000)
                    if (inIdx >= 0) {
                        val buf = codec.getInputBuffer(inIdx)!!
                        val size = extractor.readSampleData(buf, 0)
                        if (size < 0) {
                            codec.queueInputBuffer(inIdx, 0, 0, 0, MediaCodec.BUFFER_FLAG_END_OF_STREAM)
                            inputDone = true
                        } else {
                            codec.queueInputBuffer(inIdx, 0, size, extractor.sampleTime, 0)
                            extractor.advance()
                        }
                    }
                }
                val outIdx = codec.dequeueOutputBuffer(info, 10000)
                if (outIdx >= 0) {
                    val outBuf = codec.getOutputBuffer(outIdx)!!
                    if (info.size > 0) {
                        outBuf.position(info.offset)
                        outBuf.limit(info.offset + info.size)
                        val bb = ByteBuffer.allocate(info.size).order(ByteOrder.nativeOrder())
                        bb.put(outBuf)
                        bb.flip()
                        val shorts = ShortArray(info.size / 2)
                        bb.asShortBuffer().get(shorts)
                        for (s in shorts) pcmOut.add(s)
                    }
                    codec.releaseOutputBuffer(outIdx, false)
                    if (info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0) outputDone = true
                }
            }
            codec.stop(); codec.release(); extractor.release()
            return pcmOut.toShortArray() to sampleRate
        } finally {
            tmp.delete()
        }
    }

    fun chatDescribe(p: Prefs, prompt: String): String? {
        val prov = activeProvider(p) ?: return null
        return try {
            val model = when (prov.id) {
                "openai" -> "gpt-4o-mini"
                "openrouter" -> "openai/gpt-4o-mini"
                "deepseek" -> "deepseek-chat"
                "grok" -> "grok-2-latest"
                else -> "gpt-4o-mini"
            }
            val url = URL(prov.baseUrl.trimEnd('/') + "/chat/completions")
            val body = JSONObject()
                .put("model", model)
                .put("temperature", 0.3)
                .put("max_tokens", 180)
                .put("messages", JSONArray().put(JSONObject().put("role", "user").put("content", prompt)))
                .toString()
            val c = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 15000
                readTimeout = 30000
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Authorization", "Bearer ${prov.key}")
                if (prov.id == "openrouter") {
                    setRequestProperty("HTTP-Referer", "https://khanshgarzende.app")
                    setRequestProperty("X-Title", "KhanshgarZende")
                }
            }
            try {
                c.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
                if (c.responseCode !in 200..299) return null
                val txt = c.inputStream.bufferedReader().readText()
                JSONObject(txt).getJSONArray("choices").getJSONObject(0)
                    .getJSONObject("message").getString("content").trim()
            } finally {
                c.disconnect()
            }
        } catch (e: Throwable) {
            Log.e(TAG, "chatDescribe", e)
            null
        }
    }
}
''', encoding='utf-8')
print('MultiTts.kt')

sm = src / 'SpeechManager.kt'
t = sm.read_text(encoding='utf-8')
changed = False
if 'MultiTts.providers' not in t:
    t = t.replace(
        'val onlineConfigured get() = AzureTts.configured(prefs)',
        'val onlineConfigured get() = AzureTts.configured(prefs) || MultiTts.providers(prefs).isNotEmpty()',
    )
    t = t.replace(
        'private val isOnline get() = prefs.voice == "dilara" || prefs.voice == "farid"',
        'private val isOnline get() = prefs.voice == "dilara" || prefs.voice == "farid" || prefs.voice.startsWith("api:")',
    )
    t = t.replace(
        'list.add(Triple("system", "موتور صدای نصب‌شده روی گوشی", false))',
        'if (MultiTts.providers(prefs).isNotEmpty()) {\n'
        '                list.add(Triple("api:nova", "صدای آنلاین API – nova", false))\n'
        '                list.add(Triple("api:alloy", "صدای آنلاین API – alloy", false))\n'
        '                list.add(Triple("api:onyx", "صدای آنلاین API – onyx", false))\n'
        '            }\n'
        '            list.add(Triple("system", "موتور صدای نصب‌شده روی گوشی", false))',
    )
    changed = True

if 'MultiTts.synthPcm' not in t and 'private fun synth(sentence: String)' in t:
    helper = '''
    private fun multiApiSynth(sentence: String): Pair<ShortArray, Int> {
        if (prefs.voice.startsWith("api:")) {
            prefs.openaiTtsVoice = prefs.voice.removePrefix("api:")
        }
        return MultiTts.synthPcm(prefs, sentence)
    }

'''
    t = t.replace('private fun synth(sentence: String): Pair<ShortArray, Int> {', helper + '    private fun synth(sentence: String): Pair<ShortArray, Int> {')
    t2 = t.replace(
        'val (pcm, sr) = azureSynth(sentence, rate, pitch)',
        'val (pcm, sr) = if (prefs.voice.startsWith("api:")) multiApiSynth(sentence) else azureSynth(sentence, rate, pitch)',
        1,
    )
    if t2 != t:
        t = t2
        changed = True

sm.write_text(t, encoding='utf-8')
print('SpeechManager', 'changed' if changed else 'checked')

sd = src / 'SceneDescriber.kt'
st = sd.read_text(encoding='utf-8')
if 'MultiTts.chatDescribe' not in st:
    st = st.replace(
        'return Scene(sentence, key, maybeText, light < 55f)',
        '''val enriched = try {
            val pr = App.instance.prefs
            if (MultiTts.activeProvider(pr) != null) {
                val q = "به فارسی خیلی کوتاه (حداکثر دو جمله) بگو جلوی دوربین چیست. موارد: " + names.joinToString("، ")
                MultiTts.chatDescribe(pr, q)?.takeIf { it.length in 12..220 }
            } else null
        } catch (_: Throwable) { null }
        return Scene(enriched ?: sentence, key, maybeText, light < 55f)''',
    )
    sd.write_text(st, encoding='utf-8')
    print('SceneDescriber AI')

lay = res / 'layout/activity_settings.xml'
lx = lay.read_text(encoding='utf-8')
if 'et_openrouter_key' not in lx:
    block = '''
    <TextView style="@style/Label" android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:layout_marginTop="16dp" android:text="کلیدهای API (چندپلتفرم)" android:textStyle="bold"
        android:textSize="18sp" android:accessibilityHeading="true" />
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content" android:textSize="14sp"
        android:text="کلید هر سرویس را وارد کنید. Azure برای دلارا/فرید. OpenAI و سازگارها برای صدای API. OpenRouter/DeepSeek/Grok برای توضیح هوشمند." />
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content" android:text="Azure" android:textStyle="bold" />
    <EditText android:id="@+id/et_azure_key2" android:layout_width="match_parent" android:layout_height="wrap_content"
        android:hint="کلید Azure" android:inputType="textPassword" android:minHeight="48dp" />
    <EditText android:id="@+id/et_azure_region2" android:layout_width="match_parent" android:layout_height="wrap_content"
        android:hint="منطقه Azure" android:inputType="text" android:minHeight="48dp" />
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content" android:text="OpenAI" android:textStyle="bold" />
    <EditText android:id="@+id/et_openai_key" android:layout_width="match_parent" android:layout_height="wrap_content"
        android:hint="کلید OpenAI" android:inputType="textPassword" android:minHeight="48dp" />
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content" android:text="OpenRouter" android:textStyle="bold" />
    <EditText android:id="@+id/et_openrouter_key" android:layout_width="match_parent" android:layout_height="wrap_content"
        android:hint="کلید OpenRouter" android:inputType="textPassword" android:minHeight="48dp" />
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content" android:text="Google" android:textStyle="bold" />
    <EditText android:id="@+id/et_google_key" android:layout_width="match_parent" android:layout_height="wrap_content"
        android:hint="کلید Google API" android:inputType="textPassword" android:minHeight="48dp" />
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content" android:text="DeepSeek" android:textStyle="bold" />
    <EditText android:id="@+id/et_deepseek_key" android:layout_width="match_parent" android:layout_height="wrap_content"
        android:hint="کلید DeepSeek" android:inputType="textPassword" android:minHeight="48dp" />
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content" android:text="Grok / xAI" android:textStyle="bold" />
    <EditText android:id="@+id/et_grok_key" android:layout_width="match_parent" android:layout_height="wrap_content"
        android:hint="کلید Grok" android:inputType="textPassword" android:minHeight="48dp" />
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content" android:text="سفارشی" android:textStyle="bold" />
    <EditText android:id="@+id/et_custom_base" android:layout_width="match_parent" android:layout_height="wrap_content"
        android:hint="آدرس پایه API" android:inputType="textUri" android:minHeight="48dp" />
    <EditText android:id="@+id/et_custom_key" android:layout_width="match_parent" android:layout_height="wrap_content"
        android:hint="کلید سفارشی" android:inputType="textPassword" android:minHeight="48dp" />
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content" android:text="ارائه‌دهنده فعال" android:textStyle="bold" />
    <Spinner android:id="@+id/sp_online_provider" android:layout_width="match_parent" android:layout_height="48dp" android:minHeight="48dp" />
'''
    idx = lx.rfind('</LinearLayout>')
    lay.write_text(lx[:idx] + block + '\n' + lx[idx:], encoding='utf-8')
    print('layout API')

sa = src / 'SettingsActivity.kt'
st = sa.read_text(encoding='utf-8')
if 'bindMultiApiKeysV56' not in st:
    method = '''
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

'''
    if 'bindAccessibilityAndApiV55()' in st:
        st = st.replace('bindAccessibilityAndApiV55()', 'bindAccessibilityAndApiV55()\n        bindMultiApiKeysV56()')
    elif 'bindExtraSettingsV54()' in st:
        st = st.replace('bindExtraSettingsV54()', 'bindExtraSettingsV54()\n        bindMultiApiKeysV56()')
    elif 'updateBoxes()' in st:
        st = st.replace('updateBoxes()', 'bindMultiApiKeysV56()\n        updateBoxes()', 1)
    idx = st.rfind('}')
    st = st[:idx] + method + '\n' + st[idx:]
    if 'import android.widget.EditText' not in st:
        st = st.replace('import android.widget.Button', 'import android.widget.Button\nimport android.widget.EditText')
    sa.write_text(st, encoding='utf-8')
    print('SettingsActivity API')

bg = proj / 'app/build.gradle.kts'
t = bg.read_text(encoding='utf-8')
for a, b in [
    ('versionCode = 55', 'versionCode = 56'),
    ('versionCode = 54', 'versionCode = 56'),
    ('versionName = "5.5"', 'versionName = "5.6"'),
    ('versionName = "5.4"', 'versionName = "5.6"'),
]:
    t = t.replace(a, b)
bg.write_text(t, encoding='utf-8')
print('version 5.6')
print('ALL v5.6 DONE')
