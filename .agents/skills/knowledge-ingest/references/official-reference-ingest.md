# 官方 Reference 摄入

本流程承接官方文档、固定版本技术说明和可导航源码 reference。它不分析完整 Kernel/Host/CMake/Tiling 工程，也不替代尚未迁移的样例或算子 producer。

## 1. 固定来源

先选择来源模式：

- **Git Reference**：固定 canonical repo、ref、40 位 commit 和 checkout，执行下面的 inventory/ledger 流程。
- **固定归档 Reference**：确认 Registry 中的 root、fetch script、archive SHA-256 和恢复后内容树 SHA-256，运行获取脚本后直接进入 Curate；不调用 `reference_inventory.py`。获取脚本若修复归档发布器造成的正文损坏，必须先通过 archive SHA-256，再以固定文件、token 和数量执行幂等修复，并用最终 tree SHA-256 固定结果；任一漂移都失败关闭。

### Git Harvest

固定来源 checkout 后生成 inventory：

```bash
python3 <skill-dir>/scripts/reference_inventory.py inventory \
  --source-root <checkout> --repo <canonical-url> --ref <ref> \
  --scope <tracked-subtree> --output <inventory.json>
python3 <skill-dir>/scripts/reference_inventory.py scaffold-ledger \
  --inventory <inventory.json> --output <ledger.json>
```

Inventory 覆盖完整 tracked tree；`selected` 只表达本批范围，不等于已摄入。不得用文件数或目录数冒充知识覆盖。

## 2. Curate

Git 批次逐项完成 ledger；固定归档批次直接记录本次 create、update、merge、deprecate 或 defer 决定，不建立文件级账本。

Git ledger 使用：

- `ingest`：指定目标 `knowledge/...md`、受控 source role，并先用 query 查重。
- `skip`：材料不产生可复用技术知识，写明理由。
- `defer`：本批不处理、证据不足或依赖尚未迁移 producer，写明理由。

按目标 Concept 聚合多份来源。融合后写一份自包含知识，不把每个 source 拼成独立章节。已有同概念卡使用 update/merge，不重复创建变体卡。Registry 固定归档中明确登记的官方 API/Guide 是受控例外：同步器只为含独立技术事实的页面建卡，README、发布占位、纯链接目录和接口清单等导航页改由对应目录 `index.md` 承载；保留页只删除 Registry 声明的冗余章节、改写失效链接，并在正文外增加 Frontmatter 和受管关系块。当前“产品支持情况”先用于生成 `platforms`，再从正文删除。

对登记了 `mirror` 的固定归档执行：

API 的 `source_headers` 优先由源文档显式路径生成。归档没有 `include/` 源码树：无显式路径时，同步器保留同一 `primary` 文档来源卡片的已有合法补充；非法路径、重复项或来源改变时停止，不静默删除。新建卡不推测路径；新增源码补充须阅读固定版本声明并记录实际依据，不能用调用或注释中的符号命中代替声明。归档版本升级还须重新审阅这些补充，不能把路径保留当作新版本兼容证明。

```bash
python3 <skill-dir>/scripts/fixed_archive_docs.py --knowledge-root <repo> \
  sync --updated-at <UTC-second>
python3 <skill-dir>/scripts/api_operator_links.py --knowledge-root <repo> sync
```

第二条命令同时检查既有 Operator 声明的固定提交源码调用与非受管正文调用；两种证据分区展示，源码优先，展示上限与图谱自动边保持一致，超出时注明“部分算子”。同名 API 的归属必须先在完整同名集合唯一成立，不能靠平台或参数数量猜测；证据、源码校验、抽取范围、幂等和审计格式统一见[本地图谱](local-graphs.md)。源码恢复与既有来源等价本地化见[新来源接入](source-onboarding.md)。自动同步不改官方正文或外层语义关系。

Source role 只使用当前 Schema：`primary`、`supporting`、`example`、`constraint`、`header`、`implementation`、`evidence`。Git 来源固定到 40 位 commit；关键代码结论优先使用精确 blob，而不是仓库根或宽 tree。

仅以 `supporting`、`example` 等非主来源引用归档的蒸馏卡不是镜像。`sync` 的过期镜像清理、`verify` 和 `diff-check` 共用 Contract 判定：镜像采用 `primary` 来源，未标注角色的旧来源保留原有匹配行为。非主来源引用不触发镜像清理或正文空白例外；真正来源映射对应的期望卡片仍逐项校验完整元数据，不能通过改写来源角色逃避复验。

## 3. Review

由独立审阅视角核对：

- 每条关键断言能否映射到固定来源；是否出现照搬、杜撰或跨版本混写。
- path/Profile、平台、标签、生命周期与正文是否一致。
- API 的文档、声明和实现是否分清；同名 overload 是否误合并。
- update 是否保留原卡有效内容，冲突是否显式记录。
- ledger 的 ingest/skip/defer 是否覆盖 inventory 且理由成立。

最后一项只适用于 Git 批次。固定归档批次改为核对卡片 source 是否位于 Registry 登记根目录，并确认日志将记录 source ID 与 archive SHA-256。

## 4. Finalize

Git 批次运行：

```bash
python3 <skill-dir>/scripts/reference_inventory.py verify \
  --inventory <inventory.json> --ledger <ledger.json> \
  --source-root <checkout> --knowledge-root <repo> \
  --receipt <new-reference-verification.json>
```

`verify` 不只检查 ledger 形状：它先比较目标根 Contract 与本 Skill 版本且不执行目标 Python；每个 `ingest` 决策的目标卡必须已经存在、通过当前 Contract，并在 `sources` 中以相同 role 绑定 inventory 的 canonical repo、40 位 commit 和源文件 path。来源可为固定远程 blob，或能按 Registry 还原同一 repository/revision/path 的本地 Git 文件。成功 receipt 同时绑定 inventory、ledger、源 blob OID 和候选卡 SHA-256，且拒绝覆盖已有文件。缺卡、宽 tree 代替精确文件、revision/path/role 不一致都不能标记为完成。

固定归档批次不生成 inventory、ledger 或 verification receipt，只在当天日志记录 source ID、archive/tree SHA-256、created/updated/deferred 数和关键裁决。收尾必须运行 `fixed_archive_docs.py verify` 和 `api_operator_links.py verify`；前者校验恢复后内容树及已登记发布器修复状态，再按 Registry 策略重建期望卡片并复验导航过滤、章节省略、保留正文、链接和 Frontmatter，其中已有源码头文件补充仅做格式和来源绑定校验，不重新验证声明。后者重新召回明确调用并同时校验可复现审计产物（存在时）与 API 自动关系子区块。

两类批次都运行 `scripts/knowledge_ingest.py --knowledge-root <repo> sync-indexes` 同步逐层导航，并用 `--check` 验证没有陈旧 index；随后运行全库 lint、目标 query 和图谱构建。Git 批次的 inventory、ledger、verification receipt 和中间材料放在调用方实验目录或 ignored 构建目录，不写入知识正文。
