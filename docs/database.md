# 数据库设计

V0.1 使用 SQLAlchemy + SQLite，配置 `DATABASE_URL` 即可切换 PostgreSQL。

核心表：`family_members`、`health_profiles`、`health_logs`、`measurements`、`medical_visits`、`conversation_messages`、`health_documents`、`care_tasks`、`emergency_contacts`、`check_in_schedules`、`pending_actions`。

关键约束：

- `health_logs.raw_text` 永久保留老人原话；`structured_data` 只作为 AI 整理结果。
- 就医后信息保留 `feedback_source`，患者转述不能伪装成医生原始文书。
- 电话等动作先写入 `pending_actions`，确认后才执行。
- 原始医疗文件保存在 `data/uploads`，飞书同步只使用摘要和索引。

