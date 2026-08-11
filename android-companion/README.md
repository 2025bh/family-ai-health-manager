# FamilyCare Companion（Android）

这是 Android Studio 可打开的 Kotlin 基础项目。它只做电话、提醒、家属通知等“设备执行”，不保存完整健康数据库。

V0.1 的 `mockMode = true`，点击确认后只显示“模拟拨号成功”，不会真实拨号。要接真实后端时，可通过深链发送：

```text
familycare://call?name=儿子&phone=10000000000
```

手机仍会弹出第二次确认。真实拨号前还要把 `mockMode` 改为 `false` 并授予电话权限。

