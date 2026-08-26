# 质量与证据约束

本文件汇总跨 producer 通用的质量与证据约束，适用于创建和更新所有知识卡。

## 元数据一致性

- `tags`、`platforms`、`sources` 不得重复。
- `platforms` 必须与正文和固定来源证明的实际范围完全一致；未知平台使用空列表并保持 `draft`，不得根据偶然平台词猜测。
- 平台无关只在定义本身不会随硬件变化时使用 `agnostic`，不能与具体平台混用。
- 来源固定、lint 通过和单次成功都不自动生成 `verified` 事件。

## 证据合同

- 官方 Git 证据优先记录固定 revision、仓库相对 path/symbol 和精确 blob，并能把正文 claim 映射回来源。
- 开发轨迹在没有远程 Git 时，可使用带 source SHA-256 的原始记录定位、逐字 before/after、修复前失败与修复后工具观测；缺少任一关键锚点时只能 defer 或保留为待验证假设。
- GitCode/GitHub Issue/PR 证据使用对应仓库的规范工作项 URL；能定位实现时同时保留固定 base/fixed revision、实际代码变化和验证结果，Issue prose 本身不是技术事实。
- 文档、声明、实现或实验冲突时保留双方、revision 和边界，不选择更宽说法静默覆盖。

## 内容边界

- 正文保存可复用结论、条件、失效边界和验证方法；批次、diff 范围、skip 理由与执行过程进入日志/ledger。
- 正文图片使用带 40 位 commit 和具体文件路径的 HTTPS Git raw URL，不复制本地图片资产。
- 不保留 Git 冲突标记、未收敛 TODO 或大段上游原文。
- 一概念一 canonical 卡；交叉引用已有卡，不复制第二份同义内容。
- 完整样例工程、算子模板编译、轨迹进化等需要专用 producer；当前未迁移时明确 defer。
