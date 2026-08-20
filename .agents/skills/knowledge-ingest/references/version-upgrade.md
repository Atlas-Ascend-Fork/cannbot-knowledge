# 来源版本升级

适用于来源 ref、tag 或大版本切换。该流程比同 ref 增量同步多一层结构与兼容性审查。

## 流程

1. 分别固定旧、新 ref 的 40 位 commit；保留两个只读 checkout，不先推进任何“已落地”标记。
2. 生成完整树和结构 diff，区分 `new`、`update`、`deprecate`、`move_rename` 与 `structural`。
3. 将每项变化映射到现有 Concept 和目标 Profile。路径体系改变时先更新 Registry/Contract/测试并取得评审，不在摄入批次中创造临时目录。
4. active 卡使用新 revision 的精确来源；deprecated 卡保留能够支持其历史结论的旧 revision，并通过生命周期字段指向替代卡（若存在）。
5. 对平台、API 签名、实现分支、构建形态和失效边界做专项审查；版本间冲突不合并为无边界结论。
6. 完成全部卡片、导航、日志、lint、query、graph 和 inventory/ledger 对账后，才把新 revision 记录为完成。

需要专门迁移知识时，应落入当前合法的 `runbooks/<area>/` 或相关 Concept，而不是复活旧仓的 `version-migration/` 路径。
