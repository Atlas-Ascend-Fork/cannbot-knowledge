# 官方 Reference 摄入

本流程承接官方文档、固定版本技术说明和可导航源码 reference。完整 Kernel/Host/CMake/Tiling 的源码级算子分析由已接入的 VV/CV producer 承担；尚无专用 producer 的完整样例分析保持 defer。

## 1. 固定来源

先选择来源模式：

- **Git Reference**：固定 canonical repo、ref、40 位 commit 和 checkout，执行下面的 inventory/ledger 流程。
- **文档归档 Reference**：确认 Registry 中的 root、fetch script 和 `archive_url`，运行获取脚本后直接进入 Curate；不调用 `reference_inventory.py`。官方文档归档持续更新，不校验 SHA-256；获取脚本只修复已知文件中的特定代码 token 链接，不固定次数，未知损坏仍报错。缓存默认复用，显式刷新使用 `bash get_resources.sh --docs --refresh`。

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

Git 批次逐项完成 ledger；文档归档批次直接记录本次 create、update、merge、deprecate 或 defer 决定，不建立文件级账本。

Git ledger 使用：

- `ingest`：指定目标 `knowledge/...md`、受控 source role，并先用 query 查重。
- `skip`：材料不产生可复用技术知识，写明理由。
- `defer`：本批不处理、证据不足或依赖尚未迁移 producer，写明理由。

按目标 Concept 聚合多份来源。融合后写一份自包含知识，不把每个 source 拼成独立章节。已有同概念卡使用 update/merge，不重复创建变体卡。Registry 文档归档中明确登记的官方 API/Guide 是受控例外：同步器只为含独立技术事实的页面建卡，README、发布占位、纯链接目录和接口清单等导航页改由对应目录 `index.md` 承载；保留页只删除 Registry 声明的冗余章节、改写失效链接，并在正文外增加 Frontmatter 与可选的文末导航（普通知识卡链接，或「配套 API 与常见组合」小节）。当前“产品支持情况”先用于生成 `platforms`，再从正文删除。

对登记了 `mirror` 的文档归档执行：

API 的 `source_headers` 优先由源文档显式路径生成。归档没有 `include/` 源码树：无显式路径时，同步器保留同一 `primary` 文档来源卡片的已有合法补充；非法路径、重复项或来源改变时停止，不静默删除。新建卡不推测路径；新增源码补充须阅读固定版本声明并记录实际依据，不能用调用或注释中的符号命中代替声明。归档版本升级还须重新审阅这些补充，不能把路径保留当作新版本兼容证明。

```bash
python3 <skill-dir>/scripts/fixed_archive_docs.py --knowledge-root <repo> \
  sync --updated-at <UTC-second>
```

需要发现 API 引用时可按[本地图谱](local-graphs.md)按需生成源码调用建议；该步骤不回写卡片或参与入库门禁。采用的关联使用普通 Markdown 链接，镜像正文之后可追加普通链接列表，或在其后追加「配套 API 与常见组合」小节；机制说明的长度和内容边界见 AGENTS.md。源码恢复与既有来源等价本地化见[新来源接入](source-onboarding.md)。

Source role 只使用当前 Schema：`primary`、`supporting`、`example`、`constraint`、`header`、`implementation`、`evidence`。Git 来源固定到 40 位 commit；关键代码结论优先使用精确 blob，而不是仓库根或宽 tree。

仅以 `supporting`、`example` 等非主来源引用归档的蒸馏卡不是镜像。`sync` 的过期镜像清理、`verify` 和 `diff-check` 共用 Contract 判定：镜像采用 `primary` 来源，未标注角色的旧来源保留原有匹配行为。非主来源引用不触发镜像清理或正文空白例外；真正来源映射对应的期望卡片仍逐项校验完整元数据，不能通过改写来源角色逃避复验。

## 3. Review

由独立审阅视角核对：

- 每条关键断言能否映射到固定来源；是否出现照搬、杜撰或跨版本混写。
- path/Profile、平台、标签、生命周期与正文是否一致。
- API 的文档、声明和实现是否分清；同名 overload 是否误合并。
- update 是否保留原卡有效内容，冲突是否显式记录。
- ledger 的 ingest/skip/defer 是否覆盖 inventory 且理由成立。

最后一项只适用于 Git 批次。文档归档批次改为核对卡片 source 是否位于 Registry 登记根目录，并确认日志将记录 source ID、来源 URL 与本地准备时间。

## 4. Finalize

Git 批次运行：

```bash
python3 <skill-dir>/scripts/reference_inventory.py verify \
  --inventory <inventory.json> --ledger <ledger.json> \
  --source-root <checkout> --knowledge-root <repo> \
  --receipt <new-reference-verification.json>
```

`verify` 不只检查 ledger 形状：它先比较目标根 Contract 与本 Skill 版本且不执行目标 Python；每个 `ingest` 决策的目标卡必须已经存在、通过当前 Contract，并在 `sources` 中以相同 role 绑定 inventory 的 canonical repo、40 位 commit 和源文件 path。来源可为固定远程 blob，或能按 Registry 还原同一 repository/revision/path 的本地 Git 文件。成功 receipt 同时绑定 inventory、ledger、源 blob OID 和候选卡 SHA-256，且拒绝覆盖已有文件。缺卡、宽 tree 代替精确文件、revision/path/role 不一致都不能标记为完成。

文档归档批次不生成 inventory、ledger 或 verification receipt，只在当天日志记录 source ID、来源 URL、本地准备时间、created/updated/deferred 数和关键裁决。收尾必须运行 `fixed_archive_docs.py verify`；该命令检查来源完成标记及已知发布器修复状态，并校验当前来源内容，再按 Registry 策略重建期望卡片并复验导航过滤、章节省略、保留正文、链接和 Frontmatter，其中已有源码头文件补充仅做格式和来源绑定校验，不重新验证声明。API 引用建议仅在需要时单独执行。

两类批次都运行 `scripts/knowledge_ingest.py --knowledge-root <repo> sync-indexes` 同步逐层导航，并用 `--check` 验证没有陈旧 index；随后运行全库 lint、重建 Query 索引并执行目标 query；图谱构建按需执行，不作为入库步骤。Git 批次的 inventory、ledger、verification receipt 和中间材料放在调用方实验目录或 ignored 构建目录，不写入知识正文。
