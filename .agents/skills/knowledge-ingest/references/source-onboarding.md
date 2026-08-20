# 新来源接入

首次把一个上游接入本仓时读取本文件。目标是先形成可审计范围，再产出少量可校准的候选卡。

## 流程

1. 固定上游仓库、ref、40 位 commit 和纳入范围；没有固定 revision 时不开始批量摄入。
2. 运行 `reference_inventory.py inventory` 获取完整 tracked-file 清单和选中范围，随后用 `scaffold-ledger` 建决策账本。
3. 先做只读规划：列出实体、可能的目标 domain/route/Profile、重复知识和未迁移 producer；明确哪些条目 ingest、defer 或 skip。
4. 选一个中等复杂度实体试点，完成蒸馏、独立来源核验、导航、日志、lint 和 query 后再扩大范围。
5. 按语义实体分批，不按 commit 或上游文件机械分卡。同一目标卡始终单写者串行更新。
6. 收尾时运行 `reference_inventory.py verify --knowledge-root <repo> --receipt <new-json>`，确保 inventory 中每个文件都有唯一决策，且所有 ingest 决策都绑定通过 Contract 的真实候选卡和固定 source。

## 结构边界

来源不在 `knowledge/` 下建立镜像目录。目标路径只能来自当前 Registry 与 Profile；注册的空结构只用于导航完整性，不是来源 bundle 或摄入水位。

未迁移的专用 producer 在 ledger 中使用 `defer` 并写明所需 producer，不以通用卡替代。
