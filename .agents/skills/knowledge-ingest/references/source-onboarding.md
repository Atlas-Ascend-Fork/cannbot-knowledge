# 新来源接入

首次把一个 Git 上游或文档归档接入本仓时读取本文件。目标是先固定来源身份，再产出少量可校准的候选卡。

## 固定来源

- Git 来源固定 canonical repo、ref、40 位 commit 和纳入范围；没有固定 commit 时不开始批量摄入。
- 本地文档归档在 Registry 登记顶层 root、fetch script 和 HTTPS `archive_url`；先运行获取脚本恢复来源。不要为归档增加逐文件清单。

## 既有 Operator 来源本地化

已有卡仅恢复声明的固定源码并等价改写来源路径时，不属于新 Git Reference 摄入批次，不重新蒸馏技术正文或建立 inventory/ledger。先在 Registry 登记 `kind: git`、root、fetch script、规范 repository 与卡片已使用的 40 位 revisions；不得自动换成最新分支。源码与对象缓存放入 ignored 来源根，不执行上游代码。

四个算子仓的 Git 根统一为 `cann-ops-raw/ascendc/<仓库名>/`，提交快照放在其 `<40位commit>/` 下。完整根路径用于来源匹配，不能只取路径第一段；恢复时拒绝根本身或任一祖先为软链接。目录迁移必须保持 repository/revision/文件不变，并同步 Frontmatter、正文及 API 自动导航中的源码链接；本地旧索引和图谱审计不得冒充已更新结果。

```bash
python3 <skill-dir>/scripts/source_resources.py --knowledge-root <repo> fetch
python3 <skill-dir>/scripts/source_resources.py --knowledge-root <repo> verify
python3 <skill-dir>/scripts/source_resources.py --knowledge-root <repo> \
  localize --updated-at <UTC-second>
```

`fetch` 只恢复 Registry 声明的固定提交，不执行源码或 Git hooks；`verify` 不联网、不改文件。已有目录若非工具管理、来源/提交不符、有本地修改、隐藏索引项或符号链接逃逸，都失败且保留现场，不 reset、删除或覆盖。仅恢复或验证资源不迁移知识卡，也不升级来源。

知识卡的 `sources[].resource` 相对于知识仓根，正文源码链接相对于卡片目录；两者必须指向同一登记根和固定提交。离线 Lint 不会自动获取源码，也无法证明未恢复文件存在。

统一根入口同时恢复文档归档和这些源码。`localize` 在全部 checkout 通过校验后，将可用的固定远程来源及正文文件链接改为本地等价路径，不改角色、技术正文、代码围栏或普通知识链接；原提交缺失文件保留远程路径，并写 `artifacts/graphs/source_resources.json`。随后运行全库 Lint、目标 Query 和统一门禁；API 引用建议和[本地图谱](local-graphs.md)仅在需要时单独生成。新增技术断言或升级 revision 仍走对应 producer/版本流程。

## Git 批次

1. 运行 `reference_inventory.py inventory` 获取完整 tracked-file 清单和选中范围，随后用 `scaffold-ledger` 建决策账本。
2. 先做只读规划：列出实体、可能的目标 domain/route/Profile、重复知识和未迁移 producer；明确哪些条目 ingest、defer 或 skip。
3. 选一个中等复杂度实体试点，完成蒸馏、独立来源核验、导航、日志、lint 和 query 后再扩大范围。
4. 按语义实体分批，不按 commit 或上游文件机械分卡。同一目标卡始终单写者串行更新。
5. 收尾时生成不可覆盖 receipt，确保 inventory 中每个文件都有唯一决策，且 ingest 决策绑定通过 Contract 的真实候选卡和固定 source。

## 文档归档批次

1. 从 Registry 读取 source ID 与 `archive_url`，运行登记的获取脚本并完整读取本批相关源文件。
2. 先用 query 查重，再按语义实体决定 create、update、merge、deprecate 或 defer；Registry 明确登记的官方 API/Guide 由其受控转换策略筛除导航页和声明的冗余章节，其他材料不要按文件名机械建卡。
3. 先完成一个中等复杂度实体，核对正文、平台、来源和边界后再扩大范围；文档归档转换还要验证导航页只落到 `index.md`，声明章节已省略，且其余正文只发生链接目标、Frontmatter 与可选的普通链接变化。
4. 更新导航和当天日志；日志记录 source ID、来源 URL、本地准备时间、created/updated/deferred 数和关键裁决，再运行全库 lint 与目标 query。

文档归档批次不生成 inventory、ledger 或 verification receipt，也不校验 SHA-256。默认复用已完成缓存；需要更新时运行 `bash get_resources.sh --docs --refresh`。刷新只替换本地来源，不更新知识卡；正文和平台差异需审阅后再通过镜像同步和知识验证收口。

## 结构边界

来源不在 `knowledge/` 下建立镜像目录。目标路径只能来自当前 Registry 与 Profile；注册的空结构只用于导航完整性，不是来源 bundle 或摄入水位。

未迁移的专用 producer 必须 `defer` 并写明所需 producer，不以通用卡替代。
