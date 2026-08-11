# 数据库设计

V0.2 延续 SQLAlchemy + SQLite，配置 `DATABASE_URL` 即可切换 PostgreSQL。迁移版本为 `0004_health_guard`。

核心表：`family_members`、`health_profiles`、`health_logs`、`measurements`、`medical_visits`、`conversation_messages`、`health_documents`、`care_tasks`、`emergency_contacts`、`check_in_schedules`、`pending_actions`。

V0.2 增量表：

- `member_health_settings`：现代医学开关、中医开关、开启时间、知情版本和深度预留。
- `health_analysis_runs` / `health_analysis_results`：两套引擎分开保存的分析批次与分类结果。
- `health_evidence`：可追溯证据、来源类型、原文、确认状态与可信等级。
- `medical_rules`：规则 ID、版本、风险、升级动作、来源与审核状态。
- `prevention_items`：只允许绑定医生反馈、医疗资料、用户确认或医学规则的预防事项。
- `health_log_revisions`：健康日志纠错前的原文、结构化结果和风险标记。

关键约束：

- `health_logs.raw_text` 永久保留老人原话；`structured_data` 只作为 AI 整理结果。
- 就医后信息保留 `feedback_source`，患者转述不能伪装成医生原始文书。
- 电话等动作先写入 `pending_actions`，确认后才执行。
- 原始医疗文件保存在 `data/uploads`，飞书同步只使用摘要和索引。
- 分析批次采用追加保存；重新计算不会覆盖旧分析批次，也不会改写既有健康日志。
