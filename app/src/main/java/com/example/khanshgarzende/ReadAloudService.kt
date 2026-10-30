package com.example.khanshgarzende

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import android.widget.Toast

/**
 * سرویس «خواندن با صدای بلند» — خوانشگر زنده
 *
 * در تنظیمات > دسترس‌پذیری گوشی ظاهر می‌شود.
 * وقتی روشن باشد، می‌تواند متن‌های قابل‌دسترس در پیام‌رسان‌ها
 * (تلگرام، روبیکا، سروش، بله و ...) و سایر برنامه‌ها را
 * با موتور صدای خود برنامه بخواند.
 */
class ReadAloudService : AccessibilityService() {

    companion object {
        const val TAG = "ReadAloudService"
        @Volatile var instance: ReadAloudService? = null
        @Volatile var enabled = false
    }

    private val handler = Handler(Looper.getMainLooper())
    private var speech: SpeechManager? = null
    private val texts = mutableListOf<String>()
    private var index = 0
    private var speaking = false

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        enabled = true
        val info = AccessibilityServiceInfo().apply {
            eventTypes = AccessibilityEvent.TYPE_VIEW_CLICKED or
                    AccessibilityEvent.TYPE_VIEW_FOCUSED or
                    AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED or
                    AccessibilityEvent.TYPE_VIEW_TEXT_SELECTION_CHANGED or
                    AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED
            feedbackType = AccessibilityServiceInfo.FEEDBACK_SPOKEN
            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                    AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS or
                    AccessibilityServiceInfo.FLAG_REQUEST_ENHANCED_WEB_ACCESSIBILITY or
                    AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS
            notificationTimeout = 100
        }
        serviceInfo = info
        try {
            speech = SpeechManager(applicationContext)
            speech?.warmUp()
        } catch (e: Throwable) {
            Log.e(TAG, "SpeechManager init failed", e)
        }
        Log.i(TAG, "ReadAloudService connected")
        handler.post {
            Toast.makeText(this, "خواندن با صدای بلند فعال شد", Toast.LENGTH_SHORT).show()
        }
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null) return
        when (event.eventType) {
            AccessibilityEvent.TYPE_VIEW_CLICKED,
            AccessibilityEvent.TYPE_VIEW_FOCUSED,
            AccessibilityEvent.TYPE_VIEW_TEXT_SELECTION_CHANGED -> {
                val node = event.source ?: return
                try {
                    val text = extractText(node)
                    if (text.length > 2) {
                        collectNearbyTexts(node)
                        speakCurrent()
                    }
                } finally {
                    node.recycle()
                }
            }
        }
    }

    override fun onInterrupt() {
        stopSpeaking()
    }

    override fun onDestroy() {
        stopSpeaking()
        speech = null
        instance = null
        enabled = false
        super.onDestroy()
    }

    private fun extractText(node: AccessibilityNodeInfo?): String {
        if (node == null) return ""
        val sb = StringBuilder()
        node.text?.let { if (it.isNotBlank()) sb.append(it).append(' ') }
        node.contentDescription?.let { if (it.isNotBlank()) sb.append(it).append(' ') }
        for (i in 0 until node.childCount) {
            val child = node.getChild(i) ?: continue
            try {
                val t = extractText(child)
                if (t.isNotBlank()) sb.append(t).append(' ')
            } finally {
                child.recycle()
            }
        }
        return sb.toString().trim().replace(Regex("\\s+"), " ")
    }

    private fun collectNearbyTexts(node: AccessibilityNodeInfo) {
        texts.clear()
        index = 0
        val root = rootInActiveWindow ?: return
        try {
            collectTextsRecursive(root, texts)
            val current = extractText(node)
            val found = texts.indexOfFirst { it.contains(current.take(40)) || current.contains(it.take(40)) }
            if (found >= 0) index = found
        } finally {
            root.recycle()
        }
    }

    private fun collectTextsRecursive(node: AccessibilityNodeInfo?, out: MutableList<String>) {
        if (node == null) return
        val t = node.text?.toString()?.trim()
        if (!t.isNullOrBlank() && t.length > 3 && !t.matches(Regex("^[\\d\\s:./-]+$"))) {
            if (out.none { it == t }) out.add(t)
        }
        for (i in 0 until node.childCount) {
            val child = node.getChild(i) ?: continue
            try {
                collectTextsRecursive(child, out)
            } finally {
                child.recycle()
            }
        }
    }

    private fun speakCurrent() {
        if (texts.isEmpty() || index !in texts.indices) return
        val text = texts[index]
        stopSpeaking()
        speaking = true
        try {
            speech?.speak(text) {
                speaking = false
            }
        } catch (e: Throwable) {
            Log.e(TAG, "speak failed", e)
            speaking = false
        }
    }

    fun nextText() {
        if (texts.isEmpty()) return
        index = (index + 1).coerceAtMost(texts.lastIndex)
        speakCurrent()
    }

    fun prevText() {
        if (texts.isEmpty()) return
        index = (index - 1).coerceAtLeast(0)
        speakCurrent()
    }

    fun togglePause() {
        if (speaking) stopSpeaking() else speakCurrent()
    }

    private fun stopSpeaking() {
        speaking = false
        try { speech?.stop() } catch (_: Throwable) {}
    }

    fun readText(text: String) {
        if (text.isBlank()) return
        texts.clear()
        texts.add(text.trim())
        index = 0
        speakCurrent()
    }
}
