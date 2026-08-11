package cn.familycare.companion

import android.Manifest
import android.app.Activity
import android.app.AlertDialog
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast

/**
 * Companion 是执行器，不保存完整家庭医疗数据库。
 * 所有拨号动作必须在手机上再次确认；开发版默认只模拟拨号。
 */
class MainActivity : Activity() {
    private var pendingPhone: String? = null
    private var pendingName: String = "家人"
    private val mockMode = true

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(buildHome())
        handleCommand(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleCommand(intent)
    }

    private fun buildHome(): LinearLayout {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(48, 80, 48, 80)
            setBackgroundColor(Color.rgb(247, 241, 230))
        }
        root.addView(TextView(this).apply { text = "FamilyCare Companion"; textSize = 28f; gravity = Gravity.CENTER })
        root.addView(TextView(this).apply { text = "电话 · 提醒 · 家属通知执行器\n开发模式：不会真实拨号"; textSize = 18f; gravity = Gravity.CENTER; setPadding(0, 30, 0, 30) })
        root.addView(Button(this).apply { text = "模拟收到拨号指令"; textSize = 20f; setOnClickListener { confirmCall("儿子", "10000000000") } })
        return root
    }

    private fun handleCommand(intent: Intent?) {
        val uri = intent?.data ?: return
        if (uri.scheme == "familycare" && uri.host == "call") {
            confirmCall(uri.getQueryParameter("name") ?: "家人", uri.getQueryParameter("phone") ?: return)
        }
    }

    private fun confirmCall(name: String, phone: String) {
        pendingName = name
        pendingPhone = phone
        AlertDialog.Builder(this)
            .setTitle("确认拨号")
            .setMessage("确定给 $name 打电话吗？")
            .setNegativeButton("取消") { _, _ -> pendingPhone = null }
            .setPositiveButton("确定") { _, _ -> executeCall() }
            .show()
    }

    private fun executeCall() {
        val phone = pendingPhone ?: return
        if (mockMode) {
            Toast.makeText(this, "模拟拨号成功：$pendingName", Toast.LENGTH_LONG).show()
            pendingPhone = null
            return
        }
        if (checkSelfPermission(Manifest.permission.CALL_PHONE) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.CALL_PHONE), 101)
            return
        }
        startActivity(Intent(Intent.ACTION_CALL, Uri.parse("tel:$phone")))
        pendingPhone = null
    }
}

