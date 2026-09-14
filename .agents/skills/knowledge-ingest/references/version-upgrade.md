# 来源版本升级

适用于 Git 来源的 ref、tag 或大版本切换，也适用于 Registry 文档归档刷新后的结构与内容变更。该流程比同 ref 增量同步多一层结构与兼容性审查。

## Git 来源流程

1. 分别固定旧、新 ref 的 40 位 commit；保留两个只读 checkout，不先推进任何“已落地”标记。
2. 生成完整树和结构 diff，区分 `new`、`update`、`deprecate`、`move_rename` 与 `structural`。
3. 将每项变化映射到现有 Concept 和目标 Profile。路径体系改变时先更新 Registry/Contract/测试并取得评审，不在摄入批次中创造临时目录。
4. active 卡使用新 revision 的精确来源；deprecated 卡保留能够支持其历史结论的旧 revision，并通过生命周期字段指向替代卡（若存在）。
5. 对平台、API 签名、实现分支、构建形态和失效边界做专项审查；版本间冲突不合并为无边界结论。
6. 完成全部卡片、导航、日志、Lint、Query 和 inventory/ledger 对账后，才把新 revision 记录为完成；图谱只在需要查看链接关系时另行构建。

需要专门迁移知识时，应落入当前合法的 `runbooks/<area>/` 或相关 Concept，而不是复活旧仓的 `version-migration/` 路径。

## 文档归档流程

文档归档刷新前先保留旧来源供比较，再通过 `bash get_resources.sh --docs --refresh` 获取当前归档；不校验 SHA-256。审查新旧结构和正文差异，官方 API/Guide 用 `fixed_archive_docs.py sync` 重建来源映射，执行导航页过滤和章节省略，保留其余正文并改写链接目标。来源更名时先确认目标与已有卡的对应关系，再更新正文链接及 `replaced_by`；不根据文件名相似就断言接口可互换。完成镜像 `verify`、导航、Lint、Query 和日志后才记录批次完成；资源下载成功本身不表示知识同步完成。

API 的 `source_headers` 若含文档无法重建的源码审阅补充，必须对照新版本固定源码重新审阅；同一个本地文档路径可能已指向新归档，不能因来源路径字符串相同而认定补充仍有效。补充的维护与校验边界见[官方 Reference 摄入](official-reference-ingest.md)。

`mirror.upstream_revision` 用于固定来源图片及未映射为知识卡的上游文件链接，不代表滚动归档整体对应这一提交。刷新时核对这些路径在所选提交中的存在性和内容；不要让新归档中的图片或样例仍指向不包含它们的旧提交。
