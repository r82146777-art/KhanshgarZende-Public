package com.example.khanshgarzende

import android.content.Context

class Prefs(context: Context) {
    private val sp = context.getSharedPreferences("settings", Context.MODE_PRIVATE)

    var voice: String
        get() = (sp.getString("voice", "") ?: "").let {
            when (it) { "", "haaniye" -> "piper:haaniye"; "amir" -> "piper:amir"; else -> it }
        }
        set(v) = sp.edit().putString("voice", v).apply()

    var azureKey: String
        get() = sp.getString("azure_key", "") ?: ""
        set(v) = sp.edit().putString("azure_key", v.trim()).apply()

    var azureRegion: String
        get() = sp.getString("azure_region", "") ?: ""
        set(v) = sp.edit().putString("azure_region", v.trim().lowercase()).apply()

    var paginate: Boolean
        get() = sp.getBoolean("paginate", true)
        set(v) = sp.edit().putBoolean("paginate", v).apply()

    var offlineFallback: Boolean
        get() = sp.getBoolean("offline_fallback", true)
        set(v) = sp.edit().putBoolean("offline_fallback", v).apply()

    var systemEngine: String
        get() = sp.getString("system_engine", "") ?: ""
        set(v) = sp.edit().putString("system_engine", v).apply()

    var volume: Int
        get() = sp.getInt("volume", 100)
        set(v) = sp.edit().putInt("volume", v).apply()

    var rate: Int
        get() = sp.getInt("rate", 100)
        set(v) = sp.edit().putInt("rate", v).apply()

    var pitch: Int
        get() = sp.getInt("pitch", 100)
        set(v) = sp.edit().putInt("pitch", v).apply()

    var audioFormat: String
        get() = sp.getString("audio_format", "m4a") ?: "m4a"
        set(v) = sp.edit().putString("audio_format", v).apply()

    fun lastPage(id: Long) = sp.getInt("page_$id", 0)
    fun setLastPage(id: Long, p: Int) = sp.edit().putInt("page_$id", p).apply()

    var autoConvert: Boolean
        get() = sp.getBoolean("auto_convert", false)
        set(v) = sp.edit().putBoolean("auto_convert", v).apply()

    var describeScene: Boolean
        get() = sp.getBoolean("describe_scene", true)
        set(v) = sp.edit().putBoolean("describe_scene", v).apply()

    val volumeF get() = volume / 100f
    val rateF get() = rate / 100f
    val pitchF get() = pitch / 100f

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

    var unifiedApiKey: String
        get() = sp.getString("unified_api_key", "") ?: ""
        set(v) = sp.edit().putString("unified_api_key", v.trim()).apply()
    var detectedProvider: String
        get() = sp.getString("detected_provider", "") ?: ""
        set(v) = sp.edit().putString("detected_provider", v).apply()
    var apiIsPaid: Boolean
        get() = sp.getBoolean("api_is_paid", false)
        set(v) = sp.edit().putBoolean("api_is_paid", v).apply()
    var apiVoicesCsv: String
        get() = sp.getString("api_voices_csv", "") ?: ""
        set(v) = sp.edit().putString("api_voices_csv", v).apply()
    var pageTurnSound: Boolean
        get() = sp.getBoolean("page_turn_sound", true)
        set(v) = sp.edit().putBoolean("page_turn_sound", v).apply()
}
