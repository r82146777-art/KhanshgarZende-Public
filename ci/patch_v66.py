#!/usr/bin/env python3
"""v6.6: crash-hardening — no force-close on launch or settings."""
from pathlib import Path
import os, re, subprocess, sys

root = Path(__file__).resolve().parent
print("v65", subprocess.run([sys.executable, str(root / "patch_v65.py")], check=False).returncode)

proj = Path(os.environ["PROJ"])
src = proj / "app/src/main/java/com/example/khanshgarzende"

# ========== App.kt: never crash on startup; delay warmUp ==========
app = src / "App.kt"
at = app.read_text(encoding="utf-8")
at = re.sub(
    r'override fun onCreate\(\)[\s\S]*?\n    \}\n\n    companion object',
    '''override fun onCreate() {
        super.onCreate()
        try {
            Thread.setDefaultUncaughtExceptionHandler { t, e ->
                android.util.Log.e("App", "uncaught in ${t.name}", e)
            }
        } catch (_: Throwable) {}
        instance = this
        try { prefs = Prefs(this) } catch (e: Throwable) {
            android.util.Log.e("App", "prefs", e)
            prefs = Prefs(this)
        }
        try { db = LibraryDb(this) } catch (e: Throwable) {
            android.util.Log.e("App", "db", e)
        }
        try { AzureTts.init(this) } catch (e: Throwable) {
            android.util.Log.e("App", "azure", e)
        }
        try { speech = SpeechManager(this) } catch (e: Throwable) {
            android.util.Log.e("App", "speech", e)
        }
        try {
            if (Build.VERSION.SDK_INT >= 26) {
                val nm = getSystemService(NotificationManager::class.java)
                nm.createNotificationChannel(
                    NotificationChannel(CHANNEL_ID, "تبدیل متن به صوت", NotificationManager.IMPORTANCE_LOW)
                )
            }
        } catch (e: Throwable) {
            android.util.Log.e("App", "channel", e)
        }
        try {
            android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                appScope.launch(Dispatchers.IO) {
                    try { AssetInstaller.ensureInstalled(this@App) } catch (e: Throwable) {
                        android.util.Log.e("App", "assets", e)
                    }
                    try { speech.warmUp() } catch (e: Throwable) {
                        android.util.Log.e("App", "warmUp", e)
                    }
                }
            }, 2500L)
        } catch (e: Throwable) {
            android.util.Log.e("App", "schedule", e)
        }
    }

    companion object''',
    at,
    count=1,
)
app.write_text(at, encoding="utf-8")
print("App hardened")

# ========== SpeechManager: safe systemEngines + warmUp ==========
sm = src / "SpeechManager.kt"
st = sm.read_text(encoding="utf-8")

st = re.sub(
    r'fun systemEngines\(\): List<Pair<String, String>> \{[\s\S]*?\n    \}',
    '''fun systemEngines(): List<Pair<String, String>> {
        return try {
            val t = sys ?: TextToSpeech(ctx.applicationContext) {}
            val list = try { t.engines.map { it.name to it.label } } catch (_: Throwable) { emptyList() }
            if (sys == null) try { t.shutdown() } catch (_: Throwable) {}
            list
        } catch (e: Throwable) {
            Log.e(TAG, "systemEngines", e)
            emptyList()
        }
    }''',
    st,
    count=1,
)

st = re.sub(
    r'fun warmUp\(\) \{[\s\S]*?\n    \}',
    '''fun warmUp() {
        try {
            if (prefs.voice == "system") ensureSystem() else ensurePiper()
        } catch (e: Throwable) { Log.e(TAG, "warmUp", e) }
    }''',
    st,
    count=1,
)

st = re.sub(
    r'private fun ensurePiper\(\): OfflineTts \{[\s\S]*?\n    \}',
    '''private fun ensurePiper(): OfflineTts {
        synchronized(ttsLock) {
            val id = piperVoiceId
            piper?.let { if (piperId == id) return it }
            try { piper?.release() } catch (_: Throwable) {}
            piper = null
            val t = try {
                VoicePacks.create(ctx, id, THREADS)
            } catch (e: Throwable) {
                Log.e(TAG, "ensurePiper create", e)
                VoicePacks.create(ctx, "haaniye", THREADS)
            }
            piper = t; piperId = id
            return t
        }
    }''',
    st,
    count=1,
)

sm.write_text(st, encoding="utf-8")
print("SpeechManager hardened")

# ========== SettingsActivity: null-safe binds ==========
sa = src / "SettingsActivity.kt"
sat = sa.read_text(encoding="utf-8")

sat = re.sub(
    r'private fun bindSeek\(seekId: Int, labelId: Int, name: String, min: Int, max: Int, get: \(\) -> Int, set: \(Int\) -> Unit\) \{[\s\S]*?\n    \}',
    '''private fun bindSeek(seekId: Int, labelId: Int, name: String, min: Int, max: Int, get: () -> Int, set: (Int) -> Unit) {
        try {
            val seek = findViewById<SeekBar?>(seekId) ?: return
            val label = findViewById<TextView?>(labelId)
            seek.max = (max - min) / 5
            seek.progress = ((get() - min) / 5).coerceIn(0, seek.max)
            fun update(v: Int) {
                label?.text = "$name: ${fa(v)} درصد"
                seek.contentDescription = name
            }
            update(get())
            seek.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(s: SeekBar?, prog: Int, fromUser: Boolean) {
                    val v = min + prog * 5; set(v); update(v)
                }
                override fun onStartTrackingTouch(s: SeekBar?) {}
                override fun onStopTrackingTouch(s: SeekBar?) {
                    try { app.speech.speak("نمونهٔ صدا") } catch (_: Throwable) {}
                }
            })
        } catch (e: Throwable) {
            android.util.Log.e("Settings", "bindSeek", e)
        }
    }''',
    sat,
    count=1,
)

if "setContentView(R.layout.activity_settings)" in sat and "HARDENED_ONCREATE_V66" not in sat:
    sat = sat.replace(
        "setContentView(R.layout.activity_settings)\n        title = \"تنظیمات صدا\"",
        "setContentView(R.layout.activity_settings)\n        // HARDENED_ONCREATE_V66\n        title = \"تنظیمات صدا\"",
        1,
    )
    sat = sat.replace(
        'engines = listOf("" to "پیش‌فرض گوشی") + app.speech.systemEngines()',
        'engines = try { listOf("" to "پیش‌فرض گوشی") + app.speech.systemEngines() } catch (_: Throwable) { listOf("" to "پیش‌فرض گوشی") }',
        1,
    )
    sat = sat.replace(
        "val fmt = findViewById<RadioGroup>(R.id.format_group)\n        fmt.check(if (p.audioFormat == \"wav\") R.id.fmt_wav else R.id.fmt_m4a)\n        fmt.setOnCheckedChangeListener { _, id -> p.audioFormat = if (id == R.id.fmt_wav) \"wav\" else \"m4a\" }",
        """try {
            val fmt = findViewById<RadioGroup?>(R.id.format_group)
            fmt?.check(if (p.audioFormat == "wav") R.id.fmt_wav else R.id.fmt_m4a)
            fmt?.setOnCheckedChangeListener { _, id -> p.audioFormat = if (id == R.id.fmt_wav) "wav" else "m4a" }
        } catch (_: Throwable) {}""",
        1,
    )
    for sw, prop in [
        ("sw_paginate", "paginate"),
        ("sw_fallback", "offlineFallback"),
        ("sw_auto", "autoConvert"),
        ("sw_scene", "describeScene"),
    ]:
        sat = sat.replace(
            f'findViewById<SwitchCompat>(R.id.{sw}).apply {{ isChecked = p.{prop}; setOnCheckedChangeListener {{ _, c -> p.{prop} = c }} }}',
            f'try {{ findViewById<SwitchCompat?>(R.id.{sw})?.apply {{ isChecked = p.{prop}; setOnCheckedChangeListener {{ _, c -> p.{prop} = c }} }} }} catch (_: Throwable) {{}}',
        )
    sat = sat.replace(
        'findViewById<Button>(R.id.btn_test).setOnClickListener {\n            app.speech.speak("سلام. این نمونهٔ صدای خوانشگر زنده است. عدد ۱۴۰۵ را می‌خوانم.")\n        }',
        'try { findViewById<Button?>(R.id.btn_test)?.setOnClickListener {\n            try { app.speech.speak("سلام. این نمونهٔ صدای خوانشگر زنده است. عدد ۱۴۰۵ را می‌خوانم.") } catch (_: Throwable) {}\n        } } catch (_: Throwable) {}',
    )
    sat = sat.replace(
        'findViewById<Button>(R.id.btn_reset).setOnClickListener {\n            p.volume = 100; p.rate = 100; p.pitch = 100\n            recreate()\n        }',
        'try { findViewById<Button?>(R.id.btn_reset)?.setOnClickListener {\n            try { p.volume = 100; p.rate = 100; p.pitch = 100; recreate() } catch (_: Throwable) {}\n        } } catch (_: Throwable) {}',
    )

if "private fun buildVoices()" in sat:
    sat = re.sub(
        r'private fun buildVoices\(\) \{[\s\S]*?\n    \}\n\n    private fun selectVoice',
        '''private fun buildVoices() {
        try {
            group.removeAllViews()
            ignoreCheck = true
            val opts = try { SpeechManager.voiceOptions(this) } catch (_: Throwable) { emptyList() }
            for ((key, label, needDl) in opts) {
                val rb = RadioButton(this)
                rb.id = View.generateViewId()
                rb.text = label
                rb.tag = key
                rb.isChecked = (p.voice == key)
                group.addView(rb)
            }
            ignoreCheck = false
        } catch (e: Throwable) {
            android.util.Log.e("Settings", "buildVoices", e)
        }
    }

    private fun selectVoice''',
        sat,
        count=1,
    )

sa.write_text(sat, encoding="utf-8")
print("Settings braces", sat.count("{"), sat.count("}"))

bg = proj / "app/build.gradle.kts"
bt = bg.read_text(encoding="utf-8")
bt = re.sub(r"versionCode\s*=\s*\d+", "versionCode = 66", bt)
bt = re.sub(r'versionName\s*=\s*"[^"]*"', 'versionName = "6.6"', bt)
bg.write_text(bt, encoding="utf-8")
print("ALL v6.6 DONE")
