package com.example.khanshgarzende

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Matrix
import android.media.AudioManager
import android.media.ToneGenerator
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.util.Size
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.ScrollView
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.Camera
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.core.resolutionselector.ResolutionSelector
import androidx.camera.core.resolutionselector.ResolutionStrategy
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.Executors

/** اسکن پیوسته چندصد تا چند هزار صفحه با ذخیره در کتابخانه */
class BatchScanActivity : BaseActivity() {
    private lateinit var preview: PreviewView
    private lateinit var status: TextView
    private lateinit var counter: TextView
    private lateinit var textView: TextView
    private lateinit var scroll: ScrollView
    private lateinit var btnCapture: Button
    private lateinit var btnDelete: Button
    private lateinit var btnFinish: Button
    private lateinit var btnTorch: Button
    private val worker = Executors.newSingleThreadExecutor()
    private var camera: Camera? = null
    private var imageCapture: ImageCapture? = null
    private lateinit var ocr: OcrEngine
    private var torchOn = false
    @Volatile private var busy = false
    private val pages = ArrayList<String>(256)
    private var spillFile: File? = null

    private val camPerm = registerForActivityResult(ActivityResultContracts.RequestPermission()) { ok ->
        if (ok) startCamera() else {
            setStatus("اجازهٔ دوربین داده نشد")
            btnCapture.isEnabled = false
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        setContentView(R.layout.activity_batch_scan)
        preview = findViewById(R.id.batch_preview)
        status = findViewById(R.id.batch_status)
        counter = findViewById(R.id.batch_counter)
        textView = findViewById(R.id.batch_text)
        scroll = findViewById(R.id.batch_scroll)
        btnCapture = findViewById(R.id.btn_batch_capture)
        btnDelete = findViewById(R.id.btn_batch_delete)
        btnFinish = findViewById(R.id.btn_batch_finish)
        btnTorch = findViewById(R.id.btn_batch_torch)
        ocr = app.ocr
        btnCapture.setOnClickListener { capturePage() }
        btnDelete.setOnClickListener { deleteLast() }
        btnFinish.setOnClickListener { finishAndSave() }
        btnTorch.setOnClickListener { toggleTorch() }
        findViewById<Button>(R.id.btn_batch_back).setOnClickListener { confirmExit() }
        updateUi()
        spillFile = File(cacheDir, "batch_scan_${System.currentTimeMillis()}.txt")
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) startCamera()
        else camPerm.launch(Manifest.permission.CAMERA)
    }

    private fun setStatus(s: String) = runOnUiThread {
        status.text = s; status.announceForAccessibility(s)
    }

    private fun updateUi() = runOnUiThread {
        counter.text = "صفحهٔ اسکن‌شده: ${pages.size}"
        btnDelete.isEnabled = pages.isNotEmpty()
        btnFinish.isEnabled = pages.isNotEmpty()
        if (pages.isEmpty()) { textView.text = ""; scroll.visibility = View.GONE }
        else { textView.text = pages.last(); scroll.visibility = View.VISIBLE }
    }

    private fun startCamera() {
        setStatus("آماده‌سازی دوربین اسکن پیوسته…")
        worker.execute { try { ocr.init() } catch (_: Throwable) {} }
        val future = ProcessCameraProvider.getInstance(this)
        future.addListener({
            try {
                val provider = future.get()
                val p = Preview.Builder().build().also { it.setSurfaceProvider(preview.surfaceProvider) }
                imageCapture = ImageCapture.Builder()
                    .setCaptureMode(ImageCapture.CAPTURE_MODE_MAXIMIZE_QUALITY)
                    .setResolutionSelector(ResolutionSelector.Builder().setResolutionStrategy(
                        ResolutionStrategy(Size(1920, 1440), ResolutionStrategy.FALLBACK_RULE_CLOSEST_HIGHER_THEN_LOWER)).build())
                    .build()
                provider.unbindAll()
                camera = provider.bindToLifecycle(this, CameraSelector.DEFAULT_BACK_CAMERA, p, imageCapture)
                setStatus("آماده. صفحه را بگیرید و «گرفتن صفحه» را بزنید.")
            } catch (_: Throwable) { setStatus("خطا در باز کردن دوربین") }
        }, ContextCompat.getMainExecutor(this))
    }

    private fun capturePage() {
        if (busy) { toast("صبر کنید…"); return }
        val cap = imageCapture ?: run { toast("دوربین آماده نیست"); return }
        busy = true; btnCapture.isEnabled = false
        setStatus("در حال خواندن صفحه… ثابت نگه دارید")
        cap.takePicture(worker, object : ImageCapture.OnImageCapturedCallback() {
            override fun onCaptureSuccess(image: ImageProxy) {
                try {
                    val bmp = toBitmap(image); image.close()
                    handleOcr(ocr.recognize(bmp, false).text)
                } catch (_: Throwable) {
                    try { image.close() } catch (_: Throwable) {}
                    doneFail("خطا در پردازش تصویر")
                }
            }
            override fun onError(e: ImageCaptureException) = doneFail("گرفتن عکس ناموفق")
        })
    }

    private fun handleOcr(raw: String) {
        var text = raw.trim()
        try {
            text = if (app.prefs.autoCleanText) PersianText.cleanOcrText(text) else PersianText.normalize(text)
        } catch (_: Throwable) { try { text = PersianText.normalize(text) } catch (_: Throwable) {} }
        if (PersianText.letterCount(text) < 6) { doneFail("متن خوانا نیست. نور و فاصله را تنظیم کنید"); return }
        if (pages.isNotEmpty() && similarity(text, pages.last()) > 0.72f) {
            doneFail("تقریباً همان صفحهٔ قبلی است. ورق بزنید"); return
        }
        pages.add(text)
        if (pages.size % 25 == 0) try { spillFile?.writeText(pages.joinToString(Pages.SEP.toString())) } catch (_: Throwable) {}
        runOnUiThread {
            busy = false; btnCapture.isEnabled = true; updateUi()
            setStatus("صفحهٔ ${pages.size} ذخیره شد. صفحهٔ بعد یا «پایان و ذخیره».")
            beep(true)
            try { app.speech.speak("صفحهٔ ${fa(pages.size)}") } catch (_: Throwable) {}
        }
    }

    private fun doneFail(msg: String) = runOnUiThread {
        busy = false; btnCapture.isEnabled = true; setStatus(msg); beep(false)
    }

    private fun deleteLast() {
        if (pages.isEmpty()) return
        pages.removeAt(pages.lastIndex); updateUi()
        setStatus(if (pages.isEmpty()) "همه حذف شدند" else "آخرین حذف شد. تعداد: ${pages.size}")
    }

    private fun finishAndSave() {
        if (pages.isEmpty()) { toast("صفحه‌ای نیست"); return }
        if (busy) { toast("صبر کنید"); return }
        btnFinish.isEnabled = false; btnCapture.isEnabled = false
        setStatus("ذخیرهٔ ${pages.size} صفحه…")
        worker.execute {
            try {
                val cleaned = pages.map { p ->
                    try { if (app.prefs.autoCleanText) PersianText.cleanOcrText(p) else PersianText.normalize(p) }
                    catch (_: Throwable) { p }
                }
                val title = "اسکن پیوسته " + SimpleDateFormat("yyyy/MM/dd HH:mm", Locale("fa")).format(Date()) + " (${cleaned.size} صفحه)"
                val id = app.db.addPages(title, cleaned, null, "اسکن پیوسته")
                spillFile?.delete()
                runOnUiThread {
                    toast("«$title» ذخیره شد")
                    startActivity(Intent(this, TextViewerActivity::class.java).putExtra("id", id))
                    finish()
                }
            } catch (_: Throwable) {
                runOnUiThread {
                    btnFinish.isEnabled = true; btnCapture.isEnabled = true
                    setStatus("خطا در ذخیره"); toast("خطا در ذخیره")
                }
            }
        }
    }

    private fun confirmExit() {
        if (pages.isEmpty()) { finish(); return }
        android.app.AlertDialog.Builder(this)
            .setTitle("خروج")
            .setMessage("${pages.size} صفحه ذخیره نشده. خارج می‌شوید؟")
            .setPositiveButton("ذخیره و خروج") { _, _ -> finishAndSave() }
            .setNegativeButton("خروج بدون ذخیره") { _, _ -> spillFile?.delete(); finish() }
            .setNeutralButton("انصراف", null).show()
    }

    private fun toggleTorch() {
        val c = camera ?: return
        if (!c.cameraInfo.hasFlashUnit()) { toast("چراغ‌قوه ندارد"); return }
        torchOn = !torchOn
        c.cameraControl.enableTorch(torchOn)
        btnTorch.text = if (torchOn) "خاموش چراغ" else "چراغ‌قوه"
    }

    private fun toBitmap(img: ImageProxy): Bitmap {
        val b = img.toBitmap()
        val rot = img.imageInfo.rotationDegrees
        val longSide = maxOf(b.width, b.height)
        val scale = if (longSide > 3200) 3200f / longSide else 1f
        if (rot == 0 && scale == 1f) return b
        val m = Matrix().apply { postScale(scale, scale); postRotate(rot.toFloat()) }
        val out = Bitmap.createBitmap(b, 0, 0, b.width, b.height, m, true)
        if (out !== b) b.recycle()
        return out
    }

    private fun similarity(a: String, b: String): Float {
        val wa = a.split(Regex("\\s+")).filter { it.length > 1 }.toSet()
        val wb = b.split(Regex("\\s+")).filter { it.length > 1 }.toSet()
        if (wa.isEmpty() || wb.isEmpty()) return 0f
        return wa.intersect(wb).size.toFloat() / minOf(wa.size, wb.size)
    }

    private fun beep(ok: Boolean) {
        try {
            val tg = ToneGenerator(AudioManager.STREAM_MUSIC, 60)
            tg.startTone(if (ok) ToneGenerator.TONE_PROP_BEEP else ToneGenerator.TONE_PROP_NACK, 100)
            Handler(Looper.getMainLooper()).postDelayed({ try { tg.release() } catch (_: Throwable) {} }, 250)
        } catch (_: Throwable) {}
    }

    private fun fa(n: Int): String {
        val dig = charArrayOf('۰','۱','۲','۳','۴','۵','۶','۷','۸','۹')
        return n.toString().map { if (it.isDigit()) dig[it - '0'] else it }.joinToString("")
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() { confirmExit() }

    override fun onDestroy() {
        super.onDestroy()
        app.speech.stop()
        try { ocr.stop() } catch (_: Throwable) {}
        worker.shutdown()
    }
}
