# 语音设计

统一链路：`VoiceGateway → IntentRouter → FamilyCareAgent → CareTools → Database`。

`WebVoiceGateway` 已用于网页模拟器，`XiaozhiVoiceGateway`、`AndroidVoiceGateway` 和 `SmartSpeakerGateway` 是可替换入口。真实语音转文字后必须走同一业务链，不能另写一套健康数据逻辑。

