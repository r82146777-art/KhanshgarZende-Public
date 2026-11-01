#!/usr/bin/env python3
"""v6.7: root crash fix — NEVER load native TTS / heavy assets on app launch."""
from pathlib import Path
import os, re, subprocess, sys

root = Path(__file__).resolve().parent
print("v66", subprocess.run([sys.executable, str(root / "patch_v66.py")], check=False).returncode)

proj = Path(os.environ["PROJ"])
src = proj / "app/src/main/java/com/example/khanshgarzende"

# ========== App.kt: lightweight onCreate only — no warmUp, no asset copy, no native load ==========
app = src / "App.kt"
app.write_text(
    '''package com.example.khanshgarzende

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob

/**
 * Application entry. MUST stay lightweight:
 * - Do NOT load sherpa/Piper/OfflineTts here (native crash kills process; try/catch cannot catch it).
 * - Do NOT copy large assets here (OOM / LMK on low-RAM phones looks like "app closed").
 * TTS and OCR init only when the user actually uses them.
 */
class App : Application() {
    val appScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    lateinit var prefs: Prefs
    lateinit var db: LibraryDb
    lateinit var speech: SpeechManager
    val ocr: OcrEngine by lazy { OcrEngine(this) }

    override fun onCreate() {
        super.onCreate()
        instance = this
        prefs = Prefs(this)
        db = LibraryDb(this)
        try { AzureTts.init(this) } catch (_: Throwable) {}
        speech = SpeechManager(this)
        try {
            if (Build.VERSION.SDK_INT >= 26) {
                val nm = getSystemService(NotificationManager::class.java)
                nm.createNotificationChannel(
                    NotificationChannel(CHANNEL_ID, "تبدیل متن به صوت", NotificationManager.IMPORTANCE_LOW)
                )
            }
        } catch (_: Throwable) {}
        // Intentionally NO warmUp / AssetInstaller / Handler.postDelayed here.
    }

    companion object {
        const val CHANNEL_ID = "conversion"
        lateinit var instance: App
            private set
    }
}
''',
    encoding="utf-8",
)
print("App.kt rewritten — zero heavy work on launch")

# ========== SpeechManager: warmUp no-op; lazy ensurePiper ==========
sm = src / "SpeechManager.kt"
st = sm.read_text(encoding="utf-8")

st = re.sub(
    r'fun warmUp\(\) \{[\s\S]*?\n    \}',
    '''fun warmUp() {
        // no-op on purpose: loading OfflineTts at startup caused process death (native).
        // Piper is created lazily inside ensurePiper() on first speak().
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
            val threads = 1
            val t = try {
                VoicePacks.create(ctx, id, threads)
            } catch (e: Throwable) {
                Log.e(TAG, "ensurePiper primary", e)
                try {
                    VoicePacks.create(ctx, "haaniye", threads)
                } catch (e2: Throwable) {
                    Log.e(TAG, "ensurePiper fallback", e2)
                    throw e2
                }
            }
            piper = t
            piperId = id
            return t
        }
    }''',
    st,
    count=1,
)

st = re.sub(
    r'fun speak\(text: String, prefetchNext: String\? = null, onDone: \(\(Boolean\) -> Unit\)\? = null\) \{[\s\S]*?\n    \}',
    '''fun speak(text: String, prefetchNext: String? = null, onDone: ((Boolean) -> Unit)? = null) {
        if (text.isBlank()) { onDone?.invoke(true); return }
        val myGen = generation.incrementAndGet()
        speaking = true
        Thread {
            var completed = false
            try {
                if (prefs.voice == "system") speakSystem(chunksFor(text), myGen)
                else speakNatural(chunksFor(text), myGen, prefetchNext)
                completed = generation.get() == myGen
            } catch (e: Throwable) {
                Log.e(TAG, "speak", e)
            } finally {
                if (completed) speaking = false
                try { onDone?.invoke(completed) } catch (_: Throwable) {}
            }
        }.start()
    }''',
    st,
    count=1,
)

sm.write_text(st, encoding="utf-8")
print("SpeechManager: warmUp no-op, ensurePiper safer")

bg = proj / "app/build.gradle.kts"
bt = bg.read_text(encoding="utf-8")
bt = re.sub(r"versionCode\s*=\s*\d+", "versionCode = 67", bt)
bt = re.sub(r'versionName\s*=\s*"[^"]*"', 'versionName = "6.7"', bt)
bg.write_text(bt, encoding="utf-8")

at = (src / "App.kt").read_text()
assert "speech.warmUp()" not in at
assert "Handler(" not in at
assert "AssetInstaller.ensureInstalled" not in at
assert "OfflineTts(" not in at
print("VERIFY App has no heavy live calls")
print("braces App", at.count("{"), at.count("}"))
print("braces SM", st.count("{"), st.count("}"))
print("ALL v6.7 DONE")
