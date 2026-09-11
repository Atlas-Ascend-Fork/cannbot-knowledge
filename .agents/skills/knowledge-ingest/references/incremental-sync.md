# 增量同步

仅适用于已接入 Git 上游在同一 ref 上从旧 commit 推进到新 commit。首次接入走新来源流程，ref 或大版本切换走版本升级流程。固定归档不走本流程；archive SHA-256 发生变化时由当前 producer 明确 defer。

## 流程

1. 从上一批日志、决策账本和现有卡的固定 sources 确认旧 commit；缺少可靠基线时停止并请求明确起点，不猜 `HEAD~N`。
2. 固定新 commit，盘点 `old..new` 的新增、修改、删除和重命名文件，并重新生成完整 inventory。
3. 把变更映射为 `create`、`update`、`merge`、`split`、`deprecate`、`skip` 或 `defer`。删除上游内容不自动物理删除知识卡。
4. 先读原卡，再增量融合新事实；来源冲突并存记录 revision 与适用边界，不静默覆盖。
5. 对每个改动卡做独立来源核验；集中更新 index、日志、lint 和 query；本地图谱仅在需要查看时另行构建。
6. 只有全部门禁完成后，才在日志/ledger 中把新 commit 标成已落地基线。

决策按语义实体分批。同一张卡涉及多个上游 commit 或文件时合并成一个实施单元，避免重复写入。
