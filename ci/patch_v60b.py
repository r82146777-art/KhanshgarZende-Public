#!/usr/bin/env python3
"""v6.0b: OfflineAi only — minimal Settings touch, stub bindUnifiedApiV58."""
from pathlib import Path
import os, re, subprocess, sys

root = Path(__file__).resolve().parent
r = subprocess.run([sys.executable, str(root / "patch_v59b.py")], check=False)
print("v59b", r.returncode)

proj = Path(os.environ["PROJ"])
src = proj / "app/src/main/java/com/example/khanshgarzende"
res = proj / "app/src/main/res"

offline_ai = r'''package com.example.khanshgarzende

import android.content.Context
import android.graphics.Bitmap
import com.google.android.gms.tasks.Tasks
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.label.ImageLabeling
import com.google.mlkit.vision.label.defaults.ImageLabelerOptions
import java.util.concurrent.TimeUnit

/** هوش مصنوعی آفلاین: تشخیص اشیا، OCR، پاک‌سازی متن — بدون اینترنت */
object OfflineAi {
    private val labeler by lazy {
        ImageLabeling.getClient(
            ImageLabelerOptions.Builder().setConfidenceThreshold(0.40f).build()
        )
    }

    data class ObjectResult(
        val sentence: String,
        val objects: List<String>,
        val maybeText: Boolean,
        val dark: Boolean
    )

    data class OcrResult(val text: String, val cleaned: String, val confidence: Int)

    fun brightness(bmp: Bitmap): Float {
        val small = Bitmap.createScaledBitmap(bmp, 32, 32, true)
        var sum = 0L
        for (y in 0 until 32) for (x in 0 until 32) {
            val c = small.getPixel(x, y)
            sum += ((c shr 16 and 0xff) * 299 + (c shr 8 and 0xff) * 587 + (c and 0xff) * 114) / 1000
        }
        if (small !== bmp) small.recycle()
        return sum / 1024f
    }

    fun describeObjects(bmp: Bitmap): ObjectResult {
        val light = brightness(bmp)
        if (light < 28f) {
            return ObjectResult(
                "محیط خیلی تاریک است. چراغ‌قوه را روشن کنید یا به جای روشن‌تری بروید.",
                emptyList(), false, true
            )
        }
        val image = InputImage.fromBitmap(bmp, 0)
        val labels = try {
            Tasks.await(labeler.process(image), 6, TimeUnit.SECONDS)
        } catch (_: Exception) { emptyList() }
        val names = LinkedHashSet<String>()
        var maybeText = false
        for (l in labels.sortedByDescending { it.confidence }) {
            val en = l.text.lowercase()
            if (en in Labels.textHints) maybeText = true
            if (en in Labels.skip) continue
            val fa = Labels.fa(en) ?: continue
            names.add(fa)
            if (names.size >= 8) break
        }
        val list = names.toList()
        val sentence = when {
            list.isEmpty() -> "چیز مشخصی جلوی دوربین تشخیص داده نشد. دوربین را کمی جابه‌جا کنید."
            list.size == 1 -> "جلوی شما احتمالاً ${list[0]} دیده می‌شود."
            else -> {
                val joined = list.dropLast(1).joinToString("، ") + " و " + list.last()
                "جلوی شما احتمالاً $joined دیده می‌شود."
            }
        }
        return ObjectResult(sentence, list, maybeText, false)
    }

    fun ocrAndClean(ctx: Context, bmp: Bitmap, ocr: OcrEngine): OcrResult {
        if (!ocr.init()) return OcrResult("", "", 0)
        val prepared = ocr.prepare(bmp, 2200)
        val r = try { ocr.recognize(prepared, false) } catch (_: Throwable) {
            OcrEngine.Result("", 0, 0)
        }
        if (prepared !== bmp) try { prepared.recycle() } catch (_: Throwable) {}
        return OcrResult(r.text, cleanText(r.text), r.meanConf)
    }

    fun cleanText(raw: String): String {
        if (raw.isBlank()) return ""
        var t = java.text.Normalizer.normalize(raw, java.text.Normalizer.Form.NFC)
        val fa = charArrayOf('۰','۱','۲','۳','۴','۵','۶','۷','۸','۹')
        val ar = charArrayOf('٠','١','٢','٣','٤','٥','٦','٧','٨','٩')
        for (i in 0..9) {
            t = t.replace(ar[i], fa[i])
            t = t.replace(('0'.code + i).toChar(), fa[i])
        }
        t = t.replace('ي', 'ی').replace('ك', 'ک')
        t = t.replace(Regex("[\\u200c\\u200f\\u200e]+"), "\u200c")
        t = t.replace(Regex("[ \\t\\x0B\\f\\r]+"), " ")
        t = t.replace(Regex(" *\\n *"), "\n")
        t = t.replace(Regex("\\n{3,}"), "\n\n")
        t = t.replace(Regex("\\s+([،؛:!؟.])"), "$1")
        t = t.replace(Regex("([،؛:!؟.])(\\S)"), "$1 $2")
        t = t.replace(Regex("[|¦]+"), " ")
        return t.trim()
    }

    fun processDocument(text: String): String {
        var t = cleanText(text)
        t = t.replace(Regex("(?<=[.!?؟])\\s+"), "\n")
        return t.trim()
    }
}
'''
(src / "OfflineAi.kt").write_text(offline_ai, encoding="utf-8")
print("OfflineAi.kt")

sd = src / "SceneDescriber.kt"
st = sd.read_text(encoding="utf-8")
st = st.replace("setConfidenceThreshold(0.55f)", "setConfidenceThreshold(0.40f)")
st = st.replace("setConfidenceThreshold(0.5f)", "setConfidenceThreshold(0.40f)")
sd.write_text(st, encoding="utf-8")

prefs = src / "Prefs.kt"
pt = prefs.read_text(encoding="utf-8")
if "offlineAiEnabled" not in pt:
    idx = pt.rfind("}")
    prefs.write_text(pt[:idx] + '''
    var offlineAiEnabled: Boolean
        get() = sp.getBoolean("offline_ai_enabled", true)
        set(v) = sp.edit().putBoolean("offline_ai_enabled", v).apply()
''' + pt[idx:], encoding="utf-8")

layout = res / "layout" / "activity_settings.xml"
lx = layout.read_text(encoding="utf-8")
if "sw_offline_ai" not in lx:
    sw = '''
    <androidx.appcompat.widget.SwitchCompat android:id="@+id/sw_offline_ai"
        android:layout_width="match_parent" android:layout_height="64dp"
        android:text="هوش مصنوعی آفلاین (OCR و تشخیص اشیا بدون اینترنت)" android:checked="true" />
'''
    if "</LinearLayout>" in lx:
        lx = lx.replace("</LinearLayout>", sw + "\n</LinearLayout>", 1)
    else:
        lx += sw
    layout.write_text(lx, encoding="utf-8")

sa = src / "SettingsActivity.kt"
sat = sa.read_text(encoding="utf-8")
if "bindUnifiedApiV58()" in sat and "fun bindUnifiedApiV58" not in sat:
    idx = sat.rfind("}")
    stub = '''
    private fun bindUnifiedApiV58() {
        try {
            val uk = findViewById<android.widget.EditText?>(R.id.et_unified_api_key)
            uk?.setText(p.unifiedApiKey.ifBlank { p.azureKey })
            findViewById<android.widget.EditText?>(R.id.et_custom_base_url)?.setText(
                try { p.customBaseUrl } catch (_: Throwable) { "" }
            )
            findViewById<com.google.android.material.button.MaterialButton?>(R.id.btn_detect_test_key)
                ?.setOnClickListener {
                    try {
                        val key = uk?.text?.toString()?.trim().orEmpty()
                        if (key.isBlank()) {
                            findViewById<android.widget.TextView?>(R.id.tv_api_status)?.text = "کلید خالی است"
                            return@setOnClickListener
                        }
                        p.unifiedApiKey = key
                        p.azureKey = key
                        findViewById<android.widget.TextView?>(R.id.tv_api_status)?.text = "کلید ذخیره شد"
                    } catch (e: Throwable) {
                        findViewById<android.widget.TextView?>(R.id.tv_api_status)?.text = "خطا: ${e.message}"
                    }
                }
            findViewById<androidx.appcompat.widget.SwitchCompat?>(R.id.sw_page_turn_sound)?.apply {
                isChecked = p.pageTurnSound
                setOnCheckedChangeListener { _, c -> p.pageTurnSound = c }
            }
            findViewById<androidx.appcompat.widget.SwitchCompat?>(R.id.sw_offline_ai)?.apply {
                isChecked = p.offlineAiEnabled
                setOnCheckedChangeListener { _, c -> p.offlineAiEnabled = c }
            }
        } catch (_: Throwable) {}
    }
'''
    sat = sat[:idx] + stub + "\n" + sat[idx:]
    print("added bindUnifiedApiV58 stub")
elif "sw_offline_ai" not in sat:
    if "fun updateBoxes" in sat:
        sat = sat.replace(
            "fun updateBoxes",
            '''private fun bindOfflineAiSwitch() {
        try {
            findViewById<androidx.appcompat.widget.SwitchCompat?>(R.id.sw_offline_ai)?.apply {
                isChecked = p.offlineAiEnabled
                setOnCheckedChangeListener { _, c -> p.offlineAiEnabled = c }
            }
        } catch (_: Throwable) {}
    }
    fun updateBoxes''',
            1,
        )
        if "updateBoxes()" in sat and "bindOfflineAiSwitch()" not in sat:
            sat = sat.replace("updateBoxes()", "bindOfflineAiSwitch(); updateBoxes()", 1)
    print("bound offline switch via updateBoxes")
sa.write_text(sat, encoding="utf-8")
print("Settings braces", sat.count("{"), sat.count("}"))

ptf = src / "PersianText.kt"
ptt = ptf.read_text(encoding="utf-8")
if "fun offlineProcess" not in ptt:
    idx = ptt.rfind("}")
    ptf.write_text(ptt[:idx] + '''
    fun offlineProcess(text: String): String = OfflineAi.processDocument(text)
''' + ptt[idx:], encoding="utf-8")

bg = proj / "app/build.gradle.kts"
bt = bg.read_text(encoding="utf-8")
bt = re.sub(r"versionCode\s*=\s*\d+", "versionCode = 60", bt)
bt = re.sub(r'versionName\s*=\s*"[^"]*"', 'versionName = "6.0"', bt)
bg.write_text(bt, encoding="utf-8")
print("ALL v6.0b DONE")
