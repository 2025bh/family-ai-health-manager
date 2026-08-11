# 系统架构

```text
家属 Web / 老人 Web / 小智 / Android
              ↓ VoiceGateway
         Intent Router
              ↓
       FamilyCare Agent
       ↓ Context Builder
       ↓ Safety Service
       ↓ CareTools（稳定工具层）
              ↓
   SQLite / PostgreSQL 可替换数据库
       ↓          ↓          ↓
飞书 Provider  Android    本地文档存储
```

核心数据库独立于模型、飞书和硬件。小智只做语音入口，Android 只做设备执行。所有核心写操作通过 `CareTools`，避免业务逻辑散落在 Prompt 或设备代码中。

