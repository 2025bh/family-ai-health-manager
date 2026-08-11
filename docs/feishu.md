# 飞书同步

飞书不是主数据库。同步方向是：`FamilyCare DB → FeishuSyncService → 多维表格`。

目标知识库节点：`ZLGKwWARWiXyLvk5enecv1vYnVf`。如创建真实多维表格，必须创建在该节点下，不得另选位置。

当前真实 Base 已创建：[09 家医·家庭健康管家 V0.1](https://xas44uebnwx.feishu.cn/wiki/YjymwyvsMipaaTknR62cECuFn0b)，`base_token=NUXQbSoUoaawZksn4bLcJI5In7g`。

第一版映射六张表：家庭成员、健康日志、健康测量、就医记录、健康任务、检查资料索引。原始报告、处方、医疗图片不上传，只同步摘要和索引。

默认 `FEISHU_PROVIDER=mock`，无需凭证即可验收。真实同步启用前必须先读取线上真实字段 ID，保存映射并做一条测试记录的写后回读。

已完成一条纯演示成员记录的写入与回读，`member_id=demo-4`。线上 Base 目前有两个不影响同步的冗余：家庭成员表保留了 4 个默认字段；健康日志存在一个空的同名“发生时间”字段。按照项目的删除审批规则，未自动删除。
