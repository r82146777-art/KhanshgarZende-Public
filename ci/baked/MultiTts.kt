package com.example.khanshgarzende

import android.util.Log
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

object MultiTts {
    private const val TAG = "MultiTts"
    data class DetectResult(val provider: String, val label: String, val ok: Boolean, val isPaid: Boolean, val message: String, val voices: List<Pair<String, String>>, val models: List<String>)

    fun guessProvider(key: String): Pair<String, String> {
        val k = key.trim()
        return when {
            k.startsWith("sk-or-") -> "openrouter" to "OpenRouter"
            k.startsWith("sk-") && k.length > 20 -> "openai" to "OpenAI"
            k.startsWith("xai-") -> "grok" to "Grok (xAI)"
            k.startsWith("AIza") -> "google" to "Google AI"
            k.length >= 32 && k.all { it.isLetterOrDigit() } -> "azure" to "Microsoft Azure"
            else -> "openai" to "OpenAI"
        }
    }

    fun baseFor(provider: String, customBase: String = ""): String = when (provider) {
        "openai" -> "https://api.openai.com/v1"
        "openrouter" -> "https://openrouter.ai/api/v1"
        "deepseek" -> "https://api.deepseek.com/v1"
        "grok" -> "https://api.x.ai/v1"
        else -> customBase.trimEnd('/').ifBlank { "https://api.openai.com/v1" }
    }

    fun detectAndTest(key: String, customBase: String = ""): DetectResult {
        if (key.isBlank()) return DetectResult("", "", false, false, "کلید خالی است", emptyList(), emptyList())
        val (prov, label) = guessProvider(key)
        return try {
            when (prov) {
                "azure" -> testAzure(key)
                "google" -> testGoogle(key)
                else -> testOpenAiCompat(prov, label, key, customBase)
            }
        } catch (e: Exception) {
            DetectResult(prov, label, false, false, "خطا: ${e.message}", emptyList(), emptyList())
        }
    }

    private fun testAzure(key: String): DetectResult {
        for (region in listOf("eastus", "westeurope", "southeastasia", "uaenorth")) {
            try {
                val url = URL("https://$region.tts.speech.microsoft.com/cognitiveservices/voices/list")
                val c = url.openConnection() as HttpURLConnection
                c.connectTimeout = 12000; c.readTimeout = 15000
                c.setRequestProperty("Ocp-Apim-Subscription-Key", key)
                if (c.responseCode == 200) {
                    val voices = listOf(
                        "fa-IR-DilaraNeural" to "دلارا – زن فارسی (Azure)",
                        "fa-IR-FaridNeural" to "فرید – مرد فارسی (Azure)"
                    )
                    return DetectResult("azure", "Azure ($region)", true, true, "کلید Azure معتبر ($region)", voices, listOf("tts-neural"))
                }
            } catch (_: Exception) {}
        }
        return DetectResult("azure", "Azure", false, false, "کلید Azure کار نکرد", emptyList(), emptyList())
    }

    private fun testOpenAiCompat(prov: String, label: String, key: String, customBase: String): DetectResult {
        val base = baseFor(prov, customBase)
        try {
            val url = URL("$base/models")
            val c = url.openConnection() as HttpURLConnection
            c.connectTimeout = 15000; c.readTimeout = 20000
            c.setRequestProperty("Authorization", "Bearer $key")
            if (c.responseCode !in 200..299) return DetectResult(prov, label, false, false, "کلید نامعتبر (${c.responseCode})", emptyList(), emptyList())
            val data = JSONObject(c.inputStream.bufferedReader().readText()).optJSONArray("data") ?: JSONArray()
            val models = (0 until data.length()).map { data.getJSONObject(it).optString("id") }.filter { it.isNotBlank() }
            val isPaid = models.any { it.contains("gpt-4") || it.contains("pro") || it.contains("tts-1-hd") }
            val voices = listOf("nova" to "Nova", "shimmer" to "Shimmer", "alloy" to "Alloy", "echo" to "Echo", "onyx" to "Onyx", "fable" to "Fable")
            return DetectResult(prov, label, true, isPaid, "کلید $label معتبر. ${models.size} مدل.", voices, models.take(30))
        } catch (e: Exception) {
            return DetectResult(prov, label, false, false, "خطا: ${e.message}", emptyList(), emptyList())
        }
    }

    private fun testGoogle(key: String): DetectResult {
        return try {
            val url = URL("https://generativelanguage.googleapis.com/v1beta/models?key=$key")
            val c = url.openConnection() as HttpURLConnection
            c.connectTimeout = 12000; c.readTimeout = 15000
            if (c.responseCode !in 200..299) return DetectResult("google", "Google", false, false, "کلید Google نامعتبر", emptyList(), emptyList())
            DetectResult("google", "Google AI", true, false, "کلید Google معتبر", listOf("google-std" to "Google TTS"), listOf("gemini-flash"))
        } catch (e: Exception) {
            DetectResult("google", "Google", false, false, "خطا: ${e.message}", emptyList(), emptyList())
        }
    }

    fun applyDetectToPrefs(p: Prefs, r: DetectResult) {
        if (!r.ok) return
        p.detectedProvider = r.provider
        p.apiIsPaid = r.isPaid
        p.apiVoicesCsv = r.voices.joinToString("\n") { "${it.first}|${it.second}" }
        when (r.provider) {
            "azure" -> { p.azureKey = p.unifiedApiKey; p.onlineProvider = "azure" }
            "openai" -> { p.openAiApiKey = p.unifiedApiKey; p.onlineProvider = "openai" }
            "openrouter" -> { p.openRouterApiKey = p.unifiedApiKey; p.onlineProvider = "openrouter" }
            "deepseek" -> { p.deepseekApiKey = p.unifiedApiKey; p.onlineProvider = "deepseek" }
            "grok" -> { p.grokApiKey = p.unifiedApiKey; p.onlineProvider = "grok" }
            "google" -> { p.googleApiKey = p.unifiedApiKey; p.onlineProvider = "google" }
            else -> { p.customApiKey = p.unifiedApiKey; p.onlineProvider = "custom" }
        }
    }

    fun activeProvider(p: Prefs): String? {
        if (p.unifiedApiKey.isNotBlank() && p.detectedProvider.isNotBlank()) return p.detectedProvider
        if (p.azureKey.isNotBlank()) return "azure"
        if (p.openAiApiKey.isNotBlank()) return "openai"
        if (p.openRouterApiKey.isNotBlank()) return "openrouter"
        if (p.deepseekApiKey.isNotBlank()) return "deepseek"
        if (p.grokApiKey.isNotBlank()) return "grok"
        if (p.googleApiKey.isNotBlank()) return "google"
        if (p.customApiKey.isNotBlank()) return "custom"
        return null
    }

    fun keyFor(p: Prefs): String {
        if (p.unifiedApiKey.isNotBlank()) return p.unifiedApiKey
        return when (activeProvider(p)) {
            "azure" -> p.azureKey
            "openai" -> p.openAiApiKey
            "openrouter" -> p.openRouterApiKey
            "deepseek" -> p.deepseekApiKey
            "grok" -> p.grokApiKey
            "google" -> p.googleApiKey
            "custom" -> p.customApiKey
            else -> ""
        }
    }

    fun synthMp3(p: Prefs, text: String, voice: String = "nova"): ByteArray? {
        val prov = activeProvider(p) ?: return null
        val key = keyFor(p)
        if (key.isBlank() || prov == "azure") return null
        return try {
            val base = baseFor(prov, p.customApiBaseUrl)
            val url = URL("$base/audio/speech")
            val c = url.openConnection() as HttpURLConnection
            c.requestMethod = "POST"; c.doOutput = true
            c.setRequestProperty("Authorization", "Bearer $key")
            c.setRequestProperty("Content-Type", "application/json")
            val body = JSONObject().put("model", "tts-1").put("input", text.take(4000)).put("voice", voice).put("response_format", "mp3")
            c.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
            if (c.responseCode !in 200..299) null else c.inputStream.use { it.readBytes() }
        } catch (e: Exception) { Log.e(TAG, "synth", e); null }
    }

    fun chatDescribe(p: Prefs, prompt: String): String? {
        val prov = activeProvider(p) ?: return null
        val key = keyFor(p)
        if (key.isBlank() || prov == "azure" || prov == "google") return null
        return try {
            val base = baseFor(prov, p.customApiBaseUrl)
            val url = URL("$base/chat/completions")
            val c = url.openConnection() as HttpURLConnection
            c.requestMethod = "POST"; c.doOutput = true
            c.setRequestProperty("Authorization", "Bearer $key")
            c.setRequestProperty("Content-Type", "application/json")
            val model = when (prov) {
                "deepseek" -> "deepseek-chat"
                "grok" -> "grok-2-latest"
                "openrouter" -> "openai/gpt-4o-mini"
                else -> "gpt-4o-mini"
            }
            val body = JSONObject().put("model", model)
                .put("messages", JSONArray().put(JSONObject().put("role", "user").put("content", prompt)))
                .put("max_tokens", 120)
            c.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
            if (c.responseCode !in 200..299) null
            else JSONObject(c.inputStream.bufferedReader().readText()).getJSONArray("choices").getJSONObject(0).getJSONObject("message").optString("content")
        } catch (e: Exception) { null }
    }
}
