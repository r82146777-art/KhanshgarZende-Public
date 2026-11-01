#!/usr/bin/env python3
"""v6.8: fix mixed-up voices + Mana real load + no crash on speak/camera."""
from pathlib import Path
import os, re, subprocess, sys

root = Path(__file__).resolve().parent
print("v67", subprocess.run([sys.executable, str(root / "patch_v67.py")], check=False).returncode)

proj = Path(os.environ["PROJ"])
src = proj / "app/src/main/java/com/example/khanshgarzende"

vp = src / "VoicePacks.kt"
vt = vp.read_text(encoding="utf-8")

vt = re.sub(
    r"val PACKS = listOf\([\s\S]*?\)\n",
    '''val PACKS = listOf(
        Pack("amir", "امیر – مرد (آفلاین)", "vits-piper-fa_IR-amir-medium-int8", 21),
        Pack("reza", "رضا – مرد (آفلاین)", "vits-piper-fa_IR-reza_ibrahim-medium-int8", 21),
        Pack("ganji", "احمد گنجی – مرد (آفلاین)", "vits-piper-fa_IR-ganji-medium-int8", 21),
        Pack("ganji_adabi", "گنجی ادبی – مرد (آفلاین)", "vits-piper-fa_IR-ganji_adabi-medium-int8", 20),
        Pack("gyro", "گیرو – مرد (آفلاین)", "vits-piper-fa_IR-gyro-medium-int8", 21),
        Pack("mana", "مانا – زن (آفلاین، دانلود از اینترنت ~۶۴مگ)", "mana-hf", 64),
    )
''',
    vt,
    count=1,
)

new_create = '''
    fun create(ctx: Context, id: String, threads: Int): OfflineTts {
        AssetInstaller.ensureInstalled(ctx)
        val vid = when (id) {
            "mona", "mana" -> "mana"
            "musa", "khadijah" -> "haaniye"
            else -> id
        }
        if (vid == "haaniye" || !installed(ctx, vid)) {
            val cfg = OfflineTtsConfig(
                model = OfflineTtsModelConfig(
                    vits = OfflineTtsVitsModelConfig(
                        model = "voices/haaniye/model.onnx",
                        tokens = "voices/haaniye/tokens.txt",
                        dataDir = AssetInstaller.espeakDir(ctx).absolutePath,
                    ),
                    numThreads = threads.coerceIn(1, 2), debug = false, provider = "cpu",
                ),
                maxNumSentences = 1,
            )
            return OfflineTts(assetManager = ctx.assets, config = cfg)
        }
        val d = dir(ctx, vid)
        val modelFile = File(d, "model.onnx")
        val tokensFile = File(d, "tokens.txt")
        if (!modelFile.exists() || modelFile.length() < 1000L ||
            !tokensFile.exists() || tokensFile.length() < 10L
        ) {
            try { d.deleteRecursively() } catch (_: Throwable) {}
            val cfg = OfflineTtsConfig(
                model = OfflineTtsModelConfig(
                    vits = OfflineTtsVitsModelConfig(
                        model = "voices/haaniye/model.onnx",
                        tokens = "voices/haaniye/tokens.txt",
                        dataDir = AssetInstaller.espeakDir(ctx).absolutePath,
                    ),
                    numThreads = threads.coerceIn(1, 2), debug = false, provider = "cpu",
                ),
                maxNumSentences = 1,
            )
            return OfflineTts(assetManager = ctx.assets, config = cfg)
        }
        val cfg = OfflineTtsConfig(
            model = OfflineTtsModelConfig(
                vits = OfflineTtsVitsModelConfig(
                    model = modelFile.absolutePath,
                    tokens = tokensFile.absolutePath,
                    dataDir = AssetInstaller.espeakDir(ctx).absolutePath,
                ),
                numThreads = threads.coerceIn(1, 2), debug = false, provider = "cpu",
            ),
            maxNumSentences = 1,
        )
        return OfflineTts(assetManager = null, config = cfg)
    }
'''

vt = re.sub(
    r'fun create\(ctx: Context, id: String, threads: Int\): OfflineTts \{[\s\S]*?\n    \}\n\n    private fun downloadMana',
    new_create.strip() + "\n\n    private fun downloadMana",
    vt,
    count=1,
)

vp.write_text(vt, encoding="utf-8")
print("VoicePacks fixed packs + create")

sm = src / "SpeechManager.kt"
st = sm.read_text(encoding="utf-8")

st = re.sub(
    r'private fun ensurePiper\(\): OfflineTts \{[\s\S]*?\n    \}',
    '''private fun ensurePiper(): OfflineTts {
        synchronized(ttsLock) {
            var id = piperVoiceId
            if (id == "musa" || id == "khadijah" || id == "mona") {
                id = if (id == "mona") "mana" else "haaniye"
                try { prefs.voice = "piper:$id" } catch (_: Throwable) {}
            }
            piper?.let { if (piperId == id) return it }
            try { piper?.release() } catch (_: Throwable) {}
            piper = null
            val threads = 1
            val t = try {
                VoicePacks.create(ctx, id, threads)
            } catch (e: Throwable) {
                Log.e(TAG, "ensurePiper primary id=$id", e)
                try { prefs.voice = "piper:haaniye" } catch (_: Throwable) {}
                try {
                    VoicePacks.create(ctx, "haaniye", threads)
                } catch (e2: Throwable) {
                    Log.e(TAG, "ensurePiper haaniye", e2)
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

if "private fun piperSynth" in st:
    st = re.sub(
        r'private fun piperSynth\(sentence: String, rate: Float, pitch: Float\): Pair<FloatArray, Int> \{[\s\S]*?\n    \}',
        '''private fun piperSynth(sentence: String, rate: Float, pitch: Float): Pair<FloatArray, Int> {
        return try {
            val t = ensurePiper()
            val speed = (rate / pitch).coerceIn(0.25f, 4f)
            val audio = synchronized(ttsLock) { t.generate(sentence, 0, speed) }
            var s = audio.samples
            if (kotlin.math.abs(pitch - 1f) > 0.02f) s = resample(s, pitch)
            s to audio.sampleRate
        } catch (e: Throwable) {
            Log.e(TAG, "piperSynth", e)
            try { prefs.voice = "piper:haaniye"; piperId = ""; try { piper?.release() } catch (_: Throwable) {}; piper = null } catch (_: Throwable) {}
            val t = ensurePiper()
            val audio = synchronized(ttsLock) { t.generate(sentence, 0, rate.coerceIn(0.25f, 4f)) }
            audio.samples to audio.sampleRate
        }
    }''',
        st,
        count=1,
    )

sm.write_text(st, encoding="utf-8")
print("SpeechManager ensurePiper hardened")

cam = src / "CameraActivity.kt"
if cam.exists():
    ct = cam.read_text(encoding="utf-8")
    if "private fun speakThen" in ct:
        ct = re.sub(
            r'private fun speakThen\(text: String, then: \(\) -> Unit\) \{[\s\S]*?\n    \}',
            '''private fun speakThen(text: String, then: () -> Unit) {
        try {
            app.speech.speak(text) { _ -> runOnUiThread { if (!isFinishing && mode != Mode.PAUSED) then() } }
        } catch (e: Throwable) {
            android.util.Log.e("Camera", "speakThen", e)
            runOnUiThread { if (!isFinishing && mode != Mode.PAUSED) then() }
        }
    }''',
            ct,
            count=1,
        )
    cam.write_text(ct, encoding="utf-8")
    print("Camera speakThen hardened")

sa = src / "SettingsActivity.kt"
sat = sa.read_text(encoding="utf-8")
old_sv = 'private fun selectVoice(key:String){try{p.voice=key;try{app.speech.reloadVoice()}catch(e:Throwable){android.util.Log.e("S","rv",e)};try{updateBoxes()}catch(_:Throwable){}}catch(e:Throwable){android.util.Log.e("S","sv",e);toast("err")}}'
new_sv = '''private fun selectVoice(key: String) {
        try {
            p.voice = key
            try { app.speech.reloadVoice() } catch (e: Throwable) { android.util.Log.e("S", "rv", e) }
            try { updateBoxes() } catch (_: Throwable) {}
        } catch (e: Throwable) {
            android.util.Log.e("S", "sv", e)
            toast("خطا در انتخاب صدا")
        }
    }'''
if old_sv in sat:
    sat = sat.replace(old_sv, new_sv)
else:
    sat = re.sub(
        r'private fun selectVoice\([^{]+\{[\s\S]*?\n    \}\n\n    private fun askDownload',
        new_sv + "\n\n    private fun askDownload",
        sat,
        count=1,
    )
sa.write_text(sat, encoding="utf-8")
print("Settings selectVoice safe")

bg = proj / "app/build.gradle.kts"
bt = bg.read_text(encoding="utf-8")
bt = re.sub(r"versionCode\s*=\s*\d+", "versionCode = 68", bt)
bt = re.sub(r'versionName\s*=\s*"[^"]*"', 'versionName = "6.8"', bt)
bg.write_text(bt, encoding="utf-8")

vp2 = vp.read_text()
assert 'Pack("mana"' in vp2
assert 'Pack("ganji"' in vp2
assert "vits-piper-fa_IR-gyro" in vp2
print("PACKS ok, version 6.8")
print("ALL v6.8 DONE")
