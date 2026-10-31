package com.example.khanshgarzende

import android.content.Context
import com.k2fsa.sherpa.onnx.OfflineTts
import com.k2fsa.sherpa.onnx.OfflineTtsConfig
import com.k2fsa.sherpa.onnx.OfflineTtsModelConfig
import com.k2fsa.sherpa.onnx.OfflineTtsVitsModelConfig
import org.apache.commons.compress.archivers.tar.TarArchiveInputStream
import org.apache.commons.compress.compressors.bzip2.BZip2CompressorInputStream
import java.io.BufferedInputStream
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

object VoicePacks {
    class Pack(val id: String, val label: String, val file: String, val sizeMb: Int)

    private const val BASE = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/"
    val PACKS = listOf(
        Pack("amir", "امیر – مرد (آفلاین Piper)", "vits-piper-fa_IR-amir-medium-int8", 21),
        Pack("reza", "رضا – مرد (آفلاین Piper)", "vits-piper-fa_IR-reza_ibrahim-medium-int8", 21),
        Pack("ganji", "گنجی – مرد (آفلاین Piper)", "vits-piper-fa_IR-ganji-medium-int8", 21),
        Pack("ganji_adabi", "گنجی ادبی – مرد (آفلاین)", "vits-piper-fa_IR-ganji_adabi-medium-int8", 20),
        Pack("mana", "مانا / مونا – زن (آفلاین، ~۶۴ مگ)", "mana-hf", 64),
        Pack("musa", "موسی – مرد آفلاین (معادل فرید)", "vits-piper-fa_IR-amir-medium-int8", 21),
        Pack("khadijah", "خدیجه – زن آفلاین (معادل دلارا)", "vits-piper-fa_IR-ganji-medium-int8", 21),
    )

    fun dir(ctx: Context, id: String) = File(ctx.filesDir, "voices/$id")
    fun installed(ctx: Context, id: String): Boolean {
        val key = if (id == "mona") "mana" else id
        return key == "haaniye" || File(dir(ctx, key), "ok").exists()
    }
    fun installedPacks(ctx: Context) = PACKS.filter { installed(ctx, it.id) }
    fun find(id: String): Pack? {
        val key = if (id == "mona") "mana" else id
        return PACKS.firstOrNull { it.id == key }
    }

    fun download(ctx: Context, id: String, progress: (Int) -> Unit, cancelled: () -> Boolean) {
        val pack = find(id) ?: throw IllegalArgumentException(id)
        if (pack.file == "mana-hf" || id == "mana" || id == "mona") {
            downloadMana(ctx, progress, cancelled)
            return
        }
        val target = dir(ctx, id); target.deleteRecursively(); target.mkdirs()
        val tmp = File(ctx.cacheDir, "$id.tar.bz2")
        var url = URL(BASE + pack.file + ".tar.bz2")
        var conn: HttpURLConnection
        var redirects = 0
        while (true) {
            conn = url.openConnection() as HttpURLConnection
            conn.instanceFollowRedirects = false
            conn.connectTimeout = 15000; conn.readTimeout = 30000
            val code = conn.responseCode
            if (code in 300..399 && redirects < 5) {
                url = URL(url, conn.getHeaderField("Location")); conn.disconnect(); redirects++; continue
            }
            if (code != 200) throw Exception("خطای دانلود ($code)")
            break
        }
        val total = conn.contentLength.toLong().takeIf { it > 0 } ?: (pack.sizeMb * 1024L * 1024)
        conn.inputStream.use { input ->
            tmp.outputStream().use { out ->
                val buf = ByteArray(64 * 1024)
                var done = 0L; var lastPct = -1
                while (true) {
                    if (cancelled()) throw Exception("لغو شد")
                    val n = input.read(buf); if (n < 0) break
                    out.write(buf, 0, n); done += n
                    val pct = (done * 90 / total).toInt()
                    if (pct != lastPct) { lastPct = pct; progress(pct) }
                }
            }
        }
        progress(92)
        TarArchiveInputStream(BZip2CompressorInputStream(BufferedInputStream(tmp.inputStream()))).use { tar ->
            var e = tar.nextTarEntry
            while (e != null) {
                val name = e.name.substringAfterLast('/')
                if (!e.isDirectory && !e.name.contains("espeak-ng-data")) {
                    val outName = when {
                        name.endsWith(".onnx") -> "model.onnx"
                        name == "tokens.txt" -> "tokens.txt"
                        else -> null
                    }
                    if (outName != null) File(target, outName).outputStream().use { tar.copyTo(it) }
                }
                e = tar.nextTarEntry
            }
        }
        tmp.delete()
        if (!File(target, "model.onnx").exists() || !File(target, "tokens.txt").exists()) throw Exception("بستهٔ صدا ناقص است")
        File(target, "ok").writeText("1")
        progress(100)
    }

    fun delete(ctx: Context, id: String) { dir(ctx, id).deleteRecursively() }

    fun create(ctx: Context, id: String, threads: Int): OfflineTts {
        AssetInstaller.ensureInstalled(ctx)
        val vid = if (id == "mona") "mana" else id
        if (vid == "haaniye" || !installed(ctx, vid)) {
            val cfg = OfflineTtsConfig(
                model = OfflineTtsModelConfig(
                    vits = OfflineTtsVitsModelConfig(
                        model = "voices/haaniye/model.onnx",
                        tokens = "voices/haaniye/tokens.txt",
                        dataDir = AssetInstaller.espeakDir(ctx).absolutePath,
                    ),
                    numThreads = threads, debug = false, provider = "cpu",
                ),
                maxNumSentences = 1,
            )
            return OfflineTts(assetManager = ctx.assets, config = cfg)
        }
        val d = dir(ctx, vid)
        val cfg = OfflineTtsConfig(
            model = OfflineTtsModelConfig(
                vits = OfflineTtsVitsModelConfig(
                    model = File(d, "model.onnx").absolutePath,
                    tokens = File(d, "tokens.txt").absolutePath,
                    dataDir = AssetInstaller.espeakDir(ctx).absolutePath,
                ),
                numThreads = threads, debug = false, provider = "cpu",
            ),
            maxNumSentences = 1,
        )
        return OfflineTts(assetManager = null, config = cfg)
    }

    private fun downloadMana(ctx: Context, progress: (Int) -> Unit, cancelled: () -> Boolean) {
        val target = dir(ctx, "mana"); target.deleteRecursively(); target.mkdirs()
        val onnxUrl = "https://huggingface.co/MahtaFetrat/Mana-Persian-Piper/resolve/main/fa_IR-mana-medium.onnx"
        val jsonUrl = "https://huggingface.co/MahtaFetrat/Mana-Persian-Piper/resolve/main/fa_IR-mana-medium.onnx.json"
        fun downloadTo(urlStr: String, out: File, fromPct: Int, toPct: Int) {
            var url = URL(urlStr)
            var redirects = 0
            var conn: HttpURLConnection
            while (true) {
                conn = url.openConnection() as HttpURLConnection
                conn.instanceFollowRedirects = false
                conn.connectTimeout = 20000
                conn.readTimeout = 120000
                conn.setRequestProperty("User-Agent", "KhanshgarZende")
                val code = conn.responseCode
                if (code in 300..399 && redirects < 8) {
                    val loc = conn.getHeaderField("Location") ?: break
                    url = URL(url, loc); conn.disconnect(); redirects++; continue
                }
                if (code != 200) throw Exception("خطای دانلود مانا ($code)")
                break
            }
            val total = conn.contentLength.toLong().takeIf { it > 0 } ?: (60L * 1024 * 1024)
            conn.inputStream.use { input ->
                out.outputStream().use { o ->
                    val buf = ByteArray(64 * 1024)
                    var done = 0L
                    var last = -1
                    while (true) {
                        if (cancelled()) throw Exception("لغو شد")
                        val n = input.read(buf); if (n < 0) break
                        o.write(buf, 0, n); done += n
                        val pct = fromPct + ((done * (toPct - fromPct)) / total).toInt()
                        if (pct != last) { last = pct; progress(pct.coerceIn(0, 99)) }
                    }
                }
            }
            conn.disconnect()
        }
        val onnxFile = File(target, "model.onnx")
        val jsonFile = File(ctx.cacheDir, "mana.json")
        downloadTo(onnxUrl, onnxFile, 0, 85)
        downloadTo(jsonUrl, jsonFile, 85, 92)
        progress(93)
        try {
            val text = jsonFile.readText(Charsets.UTF_8)
            val map = HashMap<Int, String>()
            val re = Regex("\"((?:\\\\.|[^\"\\\\])*)\"\\s*:\\s*\\[\\s*(\\d+)")
            for (m in re.findAll(text)) {
                var ph = m.groupValues[1]
                ph = ph.replace("\\\"", "\"").replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")
                val id = m.groupValues[2].toInt()
                if (id !in map) map[id] = ph
            }
            if (map.isEmpty()) throw Exception("نقشهٔ واج‌ها خالی است")
            val maxId = map.keys.maxOrNull() ?: 0
            val sb = StringBuilder()
            for (i in 0..maxId) {
                val ph = map[i] ?: "_"
                sb.append(ph).append(' ').append(i).append('\n')
            }
            File(target, "tokens.txt").writeText(sb.toString(), Charsets.UTF_8)
        } finally {
            jsonFile.delete()
        }
        if (!onnxFile.exists() || !File(target, "tokens.txt").exists()) throw Exception("بستهٔ مانا ناقص است")
        File(target, "ok").writeText("1")
        progress(100)
    }
}
