package com.example.khanshgarzende

import android.graphics.Bitmap

/** راهنمای گویای موقعیت دوربین برای اسکن متن و توصیف محیط */
object ScanGuide {

    fun forTextScan(bmp: Bitmap?, result: OcrEngine.Result?, brightness: Float): String {
        if (brightness < 30f) {
            return "محیط تاریک است. چراغ‌قوه را روشن کنید یا به جای روشن‌تری بروید."
        }
        if (brightness < 55f) {
            return "نور کم است. کمی به سمت نور بروید یا چراغ‌قوه را روشن کنید."
        }
        if (result == null) {
            return "دوربین را روی متن بگیرید. گوشی را حدود سی سانتی‌متر بالای صفحه، صاف و ثابت نگه دارید."
        }
        val letters = PersianText.letterCount(result.text)
        val words = result.goodWords
        return when {
            letters < 3 && words < 1 ->
                "متن پیدا نشد. گوشی را کمی عقب‌تر ببرید تا کل صفحه در کادر باشد، بعد ثابت نگه دارید."
            letters < 12 || words < 2 ->
                "متن ناقص دیده می‌شود. گوشی را کمی بالاتر ببرید و صاف نگه دارید تا نوشته واضح‌تر شود."
            words in 2..4 ->
                "تقریباً خوب است. گوشی را کمی ثابت‌تر نگه دارید و یک لحظه صبر کنید."
            words >= 5 && letters >= 20 ->
                "عالی است. همین‌جا ثابت نگه دارید. متن واضح است."
            else ->
                "دوربین را صاف و ثابت بالای متن نگه دارید."
        }
    }

    fun forScene(
        brightness: Float,
        faces: Int,
        objectNames: List<String>,
        maybeText: Boolean
    ): String {
        val tips = ArrayList<String>()
        if (brightness < 30f) tips.add("محیط خیلی تاریک است؛ چراغ‌قوه را روشن کنید")
        else if (brightness < 50f) tips.add("نور کمی کم است")
        if (faces == 1) tips.add("یک نفر جلوی دوربین است. اگر می‌خواهید عکس بگیرید دکمهٔ گرفتن عکس را بزنید یا انگشت را روی تصویر نگه دارید")
        else if (faces > 1) tips.add("${PersianText.faDigits(faces)} نفر دیده می‌شوند. برای عکس، انگشت را روی تصویر نگه دارید")
        if (maybeText) tips.add("احتمالاً نوشته یا تابلو جلوی شماست. برای خواندن متن، گوشی را نزدیک‌تر و صاف بگیرید")
        if (objectNames.isNotEmpty()) {
            val joined = if (objectNames.size == 1) objectNames[0]
            else objectNames.dropLast(1).joinToString("، ") + " و " + objectNames.last()
            tips.add("جلوی شما $joined دیده می‌شود")
        }
        if (tips.isEmpty()) return "چیز مشخصی تشخیص داده نشد. گوشی را آرام به اطراف بچرخانید."
        return tips.joinToString(". ") + "."
    }
}
