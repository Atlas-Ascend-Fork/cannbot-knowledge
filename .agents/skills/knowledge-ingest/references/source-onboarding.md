# 新来源接入

首次把一个 Git 上游或固定归档接入本仓时读取本文件。目标是先固定来源身份，再产出少量可校准的候选卡。

## 固定来源

- Git 来源固定 canonical repo、ref、40 位 commit 和纳入范围；没有固定 commit 时不开始批量摄入。
- 本地固定归档在 Registry 登记顶层 root、fetch script 和 archive SHA-256；先运行获取脚本恢复来源。不要为归档增加逐文件清单。

## Git 批次

1. 运行 `reference_inventory.py inventory` 获取完整 tracked-file 清单和选中范围，随后用 `scaffold-ledger` 建决策账本。
2. 先做只读规划：列出实体、可能的目标 domain/route/Profile、重复知识和未迁移 producer；明确哪些条目 ingest、defer 或 skip。
3. 选一个中等复杂度实体试点，完成蒸馏、独立来源核验、导航、日志、lint 和 query 后再扩大范围。
4. 按语义实体分批，不按 commit 或上游文件机械分卡。同一目标卡始终单写者串行更新。
5. 收尾时生成不可覆盖 receipt，确保 inventory 中每个文件都有唯一决策，且 ingest 决策绑定通过 Contract 的真实候选卡和固定 source。

## 固定归档批次

1. 从 Registry 读取 source ID 与 archive SHA-256，运行登记的获取脚本并完整读取本批相关源文件。
2. 先用 query 查重，再按语义实体决定 create、update、merge、deprecate 或 defer；不要按文件名机械建卡。
3. 先完成一个中等复杂度实体，核对正文、平台、来源和边界后再扩大范围。
4. 更新导航和当天日志；日志记录 source ID、archive SHA-256、created/updated/deferred 数和关键裁决，再运行全库 lint 与目标 query。

固定归档批次不生成 inventory、ledger 或 verification receipt。当前流程也不自动处理 archive SHA-256 切换；遇到新归档版本时 defer，不静默替换 Registry 中的现有摘要。

## 结构边界

来源不在 `knowledge/` 下建立镜像目录。目标路径只能来自当前 Registry 与 Profile；注册的空结构只用于导航完整性，不是来源 bundle 或摄入水位。

未迁移的专用 producer 必须 `defer` 并写明所需 producer，不以通用卡替代。
