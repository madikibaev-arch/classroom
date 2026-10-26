package com.classroom.teacher

import android.annotation.SuppressLint
import android.os.Bundle
import android.view.Gravity
import android.view.ViewGroup
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import androidx.appcompat.app.AppCompatActivity

/**
 * Консоль преподавателя как Android-приложение.
 * По сути это окно, которое открывает веб-консоль сервера класса
 * (ту же, что в браузере), запоминает адрес сервера и показывает
 * экраны учеников с управлением в реальном времени.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var web: WebView
    private lateinit var addr: EditText

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val prefs = getSharedPreferences("cfg", MODE_PRIVATE)

        val root = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }

        // Верхняя строка: поле адреса сервера + кнопка «Открыть»
        val bar = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(12, 12, 12, 12)
        }
        addr = EditText(this).apply {
            hint = "IP сервера, напр. 192.168.1.10:8080"
            setText(prefs.getString("addr", ""))
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        }
        val btn = Button(this).apply { text = "Открыть" }
        bar.addView(addr)
        bar.addView(btn)

        // Веб-область с консолью
        web = WebView(this).apply {
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f
            )
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.mediaPlaybackRequiresUserGesture = false
            webViewClient = WebViewClient()
            webChromeClient = WebChromeClient()
        }

        root.addView(bar)
        root.addView(web)
        setContentView(root)

        btn.setOnClickListener {
            val raw = addr.text.toString().trim()
            if (raw.isEmpty()) return@setOnClickListener
            prefs.edit().putString("addr", raw).apply()
            web.loadUrl(toUrl(raw))
        }

        val saved = prefs.getString("addr", "").orEmpty()
        if (saved.isNotEmpty()) {
            web.loadUrl(toUrl(saved))
        }
    }

    private fun toUrl(a: String): String =
        if (a.startsWith("http://") || a.startsWith("https://")) a else "http://$a"

    @Suppress("DEPRECATION")
    override fun onBackPressed() {
        if (web.canGoBack()) web.goBack() else super.onBackPressed()
    }
}
