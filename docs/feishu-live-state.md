# 飞书线上状态（2026-08-09）

- 父节点：`03 大健康｜慢病管理与中医自学`
- 父节点 token：`ZLGKwWARWiXyLvk5enecv1vYnVf`
- 空间 ID：`7611364986664799460`
- Base：[09 家医·家庭健康管家 V0.1](https://xas44uebnwx.feishu.cn/wiki/YjymwyvsMipaaTknR62cECuFn0b)
- Base token：`NUXQbSoUoaawZksn4bLcJI5In7g`

## 六张表

| 表名 | table_id |
|---|---|
| 家庭成员 | `tbl9K7ygKShdsvXr` |
| 健康日志 | `tblVqOVwgW9i1oCr` |
| 健康测量 | `tblh9hkEovDZr59z` |
| 就医记录 | `tblQNxeM04X7kjw2` |
| 健康任务 | `tblLLdQ1WL3qlQgL` |
| 检查资料索引 | `tblHACY98Tg8VAMP` |

## 写入回读证据

家庭成员表已写入纯演示记录：

- record_id：`recvrJ9V1Ujt0n`
- member_id：`demo-4`
- 姓名：爷爷
- 关系：祖父
- 回读结果与写入值一致

## 待审批清理

以下内容不影响同步，但涉及删除，未自动处理：

1. 家庭成员表创建时平台自带的 `Text`、`Single option`、`Date`、`Attachment` 字段。
2. 健康日志表因新建后的短暂一致性延迟出现两个同名“发生时间”字段，其中一个为空。

