# 官方 Reference 摄入

本流程承接官方文档、固定版本技术说明和可导航源码 reference。它不分析完整 Kernel/Host/CMake/Tiling 工程，也不替代尚未迁移的样例或算子 producer。

## 1. 固定来源

先选择来源模式：

- **Git Reference**：固定 canonical repo、ref、40 位 commit 和 checkout，执行下面的 inventory/ledger 流程。
- **固定归档 Reference**：确认 Registry 中的 root、fetch script 和 archive SHA-256，运行获取脚本后直接进入 Curate；不调用 `reference_inventory.py`。

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

按目标 Concept 聚合多份来源。融合后写一份自包含知识，不把每个 source 拼成独立章节。已有同概念卡使用 update/merge，不重复创建变体卡。

Source role 只使用当前 Schema：`primary`、`supporting`、`example`、`constraint`、`header`、`implementation`、`evidence`。Git 来源固定到 40 位 commit；关键代码结论优先使用精确 blob，而不是仓库根或宽 tree。

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

`verify` 不只检查 ledger 形状：它先比较目标根 Contract 与本 Skill 版本且不执行目标 Python；每个 `ingest` 决策的目标卡必须已经存在、通过当前 Contract，并在 `sources` 中以相同 role 绑定 inventory 的 canonical repo、40 位 commit 和源文件 path。成功 receipt 同时绑定 inventory、ledger、源 blob OID 和候选卡 SHA-256，且拒绝覆盖已有文件。缺卡、宽 tree 代替精确文件、revision/path/role 不一致都不能标记为完成。

固定归档批次不生成 inventory、ledger 或 verification receipt，只在当天日志记录 source ID、archive SHA-256、created/updated/deferred 数和关键裁决。

两类批次都运行 `scripts/knowledge_ingest.py --knowledge-root <repo> sync-indexes` 同步逐层导航，并用 `--check` 验证没有陈旧 index；随后运行全库 lint、目标 query 和图谱构建。Git 批次的 inventory、ledger、verification receipt 和中间材料放在调用方实验目录或 ignored 构建目录，不写入知识正文。
