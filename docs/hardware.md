# 小智与硬件

推荐对接 `xiaozhi-esp32 + xiaozhi-esp32-server`，但小智仅是语音和设备入口，不保存核心家庭健康数据。

当前已提供 `XiaozhiVoiceGateway` 协议边界。未来由小智服务器把识别文本 POST 到 `/api/voice/message`，并设置 `gateway=xiaozhi` 即可。正式部署前需单独完成网络安全、鉴权、传输加密和设备身份审核。

