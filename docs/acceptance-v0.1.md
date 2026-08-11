# FamilyCare AI V0.1 验收记录

最近验收：2026-08-11（Asia/Shanghai）

## P0 闭环

| 要求 | 结果 | 证据 |
|---|---|---|
| 看医生模式 | 通过 | 8 步逐题对话，结构化区分复诊/初诊，支持核对修改，`PREPARING → REVIEWING → READY → VISITED` |
| 就医回来模式 | 通过 | 来源保存为 `doctor_reported_by_patient`，识别“两周后复查”并生成任务 |
| 自然语言健康日志 | 通过 | 原话与结构化 JSON 双存；“胸口不得劲”回归测试通过 |
| 长期健康时间线 | 通过 | 合并日志、测量、就医、任务和文档；支持搜索、筛选、按日折叠和分批显示 |
| 就医摘要 | 通过 | 原医生近期精简版 / 新医生详细版 + A4 打印，历史异常与当前状态分开 |

## P1 能力

| 要求 | 结果 | 边界 |
|---|---|---|
| AI 主动询问 | 通过 | 时间可配置；检查今日已有记录；支持 `skip_today` / `snooze_until` |
| 普通电话联系人 | 通过 | 解析联系人并二次确认；当前 Mock 拨号 |
| 家属通知 | 通过 | 必须 `confirm=true`；当前 Mock 通知 |
| 飞书同步 | 通过 | 真实 Base 六表已创建，演示记录写入回读；运行时默认 Mock，配置凭证可启用 OpenAPI Provider |

## P2 预留接口

- 小智：`XiaozhiVoiceGateway`
- 家庭视频：`VideoCallProvider` / `WebRTCVideoCallProvider`
- OCR/多模态：`DocumentParserProvider` / `VisionLLMDocumentParser`
- 慢病趋势：长期时间线与 30 天上下文已经提供数据基础，复杂趋势分析留到 V0.2

## 安全与隐私

- 独立 `SafetyService`，可能紧急时停止普通聊天。
- 不提供 AI 诊断、处方、停药或改剂量能力。
- 用药/医生记录修改、电话和家属通知需要二次确认。
- V0.1 不提供删除健康记录接口。
- 原始医疗文件仅保存在本地，飞书只同步摘要和索引。
- 否定症状不误报：“最近没有黑便、便血”不触发风险；后文出现当前阳性症状仍触发提醒。

## 自动与运行验收

- `scripts/test-windows.ps1`：37 个后端测试通过，前端生产构建通过。
- Python `compileall`：通过。
- Alembic：`0003_member_profile_and_medication_courses (head)`。
- 一键启动后：`GET /api/health` 返回 `ok`，首页返回 HTTP 200。
- 真实 API Demo：血糖追问、看医生摘要、就医后复查任务、电话确认、家属通知均通过。
- 视觉验收：当前页面截图集中位于 `docs/智能管家网站复盘/`，包括首页、时间线、检查资料、原图预览、就医报告和中药疗程。

## 已知但不阻塞的问题

飞书线上表存在两个不影响同步的冗余，因删除必须审批而保留：

1. 家庭成员表的 4 个平台默认字段。
2. 健康日志表一个空的重复“发生时间”字段。
