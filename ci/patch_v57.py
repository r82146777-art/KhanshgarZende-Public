#!/usr/bin/env python3
"""v5.7: add Mana offline Persian voice + ganji_adabi; more offline FA packs."""
from pathlib import Path
import os
import subprocess
import sys

root = Path(__file__).resolve().parent
for name in ('patch_v56.py', 'patch_v56b.py'):
    p = root / name
    if p.exists():
        r = subprocess.run([sys.executable, str(p)], check=False)
        print(name, 'exit', r.returncode)

proj = Path(os.environ['PROJ'])
src = proj / 'app/src/main/java/com/example/khanshgarzende'
vp = src / 'VoicePacks.kt'
t = vp.read_text(encoding='utf-8')

old_packs = '''val PACKS = listOf(
        Pack("amir", "امیر (صدای طبیعی مرد)", "vits-piper-fa_IR-amir-medium-int8", 21),
        Pack("gyro", "ژیرو (صدای طبیعی مرد)", "vits-piper-fa_IR-gyro-medium-int8", 21),
        Pack("reza", "رضا (صدای طبیعی مرد)", "vits-piper-fa_IR-reza_ibrahim-medium-int8", 21),
        Pack("ganji", "گنجی (صدای طبیعی مرد)", "vits-piper-fa_IR-ganji-medium-int8", 21),
    )'''

new_packs = '''val PACKS = listOf(
        Pack("amir", "امیر – مرد (آفلاین)", "vits-piper-fa_IR-amir-medium-int8", 21),
        Pack("gyro", "ژیرو – مرد (آفلاین)", "vits-piper-fa_IR-gyro-medium-int8", 21),
        Pack("reza", "رضا – مرد (آفلاین)", "vits-piper-fa_IR-reza_ibrahim-medium-int8", 21),
        Pack("ganji", "گنجی – مرد (آفلاین)", "vits-piper-fa_IR-ganji-medium-int8", 21),
        Pack("ganji_adabi", "گنجی ادبی – مرد (آفلاین)", "vits-piper-fa_IR-ganji_adabi-medium-int8", 20),
        Pack("mana", "مانا / مونا – زن (آفلاین، دانلود ~۶۴ مگ)", "mana-hf", 64),
    )'''

if 'Pack("mana"' not in t:
    if old_packs in t:
        t = t.replace(old_packs, new_packs)
    else:
        t = t.replace(
            'Pack("ganji", "گنجی (صدای طبیعی مرد)", "vits-piper-fa_IR-ganji-medium-int8", 21),\n    )',
            'Pack("ganji", "گنجی – مرد (آفلاین)", "vits-piper-fa_IR-ganji-medium-int8", 21),\n'
            '        Pack("ganji_adabi", "گنجی ادبی – مرد (آفلاین)", "vits-piper-fa_IR-ganji_adabi-medium-int8", 20),\n'
            '        Pack("mana", "مانا / مونا – زن (آفلاین، دانلود ~۶۴ مگ)", "mana-hf", 64),\n'
            '    )',
        )
    print('PACKS updated')
else:
    print('mana already in PACKS')

if 'downloadMana' not in t:
    old_dl = '''fun download(ctx: Context, id: String, progress: (Int) -> Unit, cancelled: () -> Boolean) {
        val pack = find(id) ?: throw IllegalArgumentException(id)
        val target = dir(ctx, id); target.deleteRecursively(); target.mkdirs()
        val tmp = File(ctx.cacheDir, "$id.tar.bz2")
        var url = URL(BASE + pack.file + ".tar.bz2")'''
    new_dl = '''fun download(ctx: Context, id: String, progress: (Int) -> Unit, cancelled: () -> Boolean) {
        val pack = find(id) ?: throw IllegalArgumentException(id)
        if (pack.file == "mana-hf" || id == "mana" || id == "mona") {
            downloadMana(ctx, progress, cancelled)
            return
        }
        val target = dir(ctx, id); target.deleteRecursively(); target.mkdirs()
        val tmp = File(ctx.cacheDir, "$id.tar.bz2")
        var url = URL(BASE + pack.file + ".tar.bz2")'''
    if old_dl in t:
        t = t.replace(old_dl, new_dl)
    else:
        t = t.replace(
            'fun download(ctx: Context, id: String, progress: (Int) -> Unit, cancelled: () -> Boolean) {\n'
            '        val pack = find(id) ?: throw IllegalArgumentException(id)\n',
            'fun download(ctx: Context, id: String, progress: (Int) -> Unit, cancelled: () -> Boolean) {\n'
            '        val pack = find(id) ?: throw IllegalArgumentException(id)\n'
            '        if (pack.file == "mana-hf" || id == "mana" || id == "mona") {\n'
            '            downloadMana(ctx, progress, cancelled)\n'
            '            return\n'
            '        }\n',
        )

    t = t.replace(
        'fun find(id: String) = PACKS.firstOrNull { it.id == id }',
        'fun find(id: String): Pack? {\n'
        '        val key = if (id == "mona") "mana" else id\n'
        '        return PACKS.firstOrNull { it.id == key }\n'
        '    }',
    )
    t = t.replace(
        'fun installed(ctx: Context, id: String) = id == "haaniye" || File(dir(ctx, id), "ok").exists()',
        'fun installed(ctx: Context, id: String): Boolean {\n'
        '        val key = if (id == "mona") "mana" else id\n'
        '        return key == "haaniye" || File(dir(ctx, key), "ok").exists()\n'
        '    }',
    )
    t = t.replace(
        'fun create(ctx: Context, id: String, threads: Int): OfflineTts {\n'
        '        AssetInstaller.ensureInstalled(ctx)\n'
        '        if (id == "haaniye" || !installed(ctx, id)) {',
        'fun create(ctx: Context, id: String, threads: Int): OfflineTts {\n'
        '        AssetInstaller.ensureInstalled(ctx)\n'
        '        val vid = if (id == "mona") "mana" else id\n'
        '        if (vid == "haaniye" || !installed(ctx, vid)) {',
    )
    if 'val vid = if (id == "mona") "mana" else id' in t:
        t = t.replace(
            'val d = dir(ctx, id)\n'
            '        val cfg = OfflineTtsConfig(\n'
            '            model = OfflineTtsModelConfig(\n'
            '                vits = OfflineTtsVitsModelConfig(\n'
            '                    model = File(d, "model.onnx").absolutePath,\n'
            '                    tokens = File(d, "tokens.txt").absolutePath,',
            'val d = dir(ctx, vid)\n'
            '        val cfg = OfflineTtsConfig(\n'
            '            model = OfflineTtsModelConfig(\n'
            '                vits = OfflineTtsVitsModelConfig(\n'
            '                    model = File(d, "model.onnx").absolutePath,\n'
            '                    tokens = File(d, "tokens.txt").absolutePath,',
        )

    mana_fn = r'''
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

'''
    idx = t.rfind('}')
    t = t[:idx] + mana_fn + '\n' + t[idx:]
    print('downloadMana added')

vp.write_text(t, encoding='utf-8')
print('VoicePacks.kt written')

sm = src / 'SpeechManager.kt'
st = sm.read_text(encoding='utf-8')
if 'هانیه – صدای طبیعی زن' in st:
    st = st.replace(
        'هانیه – صدای طبیعی زن (آفلاین، داخل برنامه)',
        'هانیه – زن (آفلاین، داخل برنامه)',
    )
    sm.write_text(st, encoding='utf-8')

bg = proj / 'app/build.gradle.kts'
bt = bg.read_text(encoding='utf-8')
for a, b in [
    ('versionCode = 56', 'versionCode = 57'),
    ('versionCode = 55', 'versionCode = 57'),
    ('versionName = "5.6"', 'versionName = "5.7"'),
    ('versionName = "5.5"', 'versionName = "5.7"'),
]:
    bt = bt.replace(a, b)
bg.write_text(bt, encoding='utf-8')
print('version 5.7')
print('ALL v5.7 DONE')
