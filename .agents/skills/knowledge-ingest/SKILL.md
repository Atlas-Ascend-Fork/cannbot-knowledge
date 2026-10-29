---
name: knowledge-ingest
description: 将 cannbot-knowledge 摄入请求统一路由，把官方文档归档 API/Guide 受控转换为知识卡，或将固定版本源码、人工材料蒸馏为符合 OKF v0.2 与 CANNBot Profile 的候选卡。接入来源、按 commit 增量同步、升级版本、建卡和更新知识时使用；支持按需查看链接图谱或生成 API 与算子的引用建议。
---

# Knowledge Ingest

本 Skill 是通用摄入路由入口。先判断变化类型和来源类型，再执行已接入 producer；任务已明确时也可直接调用对应的 VV/CV producer，或按 `ops-knowledge-trace-ingest` 的手动触发词在本知识仓启动 trace producer。通用路由和直接调用都遵守对应 producer 的证据、写入边界与外层收尾门禁。

## 路由

1. 判断来源与生命周期：首次接入读[新来源接入](references/source-onboarding.md)；Git 同 ref 推进读[增量同步](references/incremental-sync.md)，Git ref/大版本切换读[版本升级](references/version-upgrade.md)；Registry 登记的文档归档执行官方 Reference 中的直接流程，不调用 Git inventory 工具。
2. 判断 producer：
   - 官方文档、技术 reference、固定版本源码说明：执行[官方 Reference 摄入](references/official-reference-ingest.md)。
   - 已经蒸馏好的人工材料或单张候选：使用本 Skill 的 `create` 流程。
   - 算子开发 trace、会话日志或已归一化事件流：在本知识仓路由到 [`ops-knowledge-trace-ingest`](../ops-knowledge-trace-ingest/SKILL.md)；业务项目的 contributor 安装不携带该仓内 producer，此时记录 `defer` 并说明需在独立知识仓执行。
   - 源码级完整算子知识：冻结逻辑算子、固定 commit、入口、平台和目标卡；至少一个 Host/launcher 可达 Device 节点含 Cube/AIC 或 MIX_CV 时使用 [`ops-knowledge-cv-ingest`](../ops-knowledge-cv-ingest/SKILL.md)，全部可达节点均不含上述类型时使用 [`ops-knowledge-vv-ingest`](../ops-knowledge-vv-ingest/SKILL.md)。这两项 producer 已接入，只提取源码知识，不执行编译或真机测试。
   - 尚无专用 producer 的完整样例分析、Issue/PR 证据编译：记录 `defer` 原因；已有人工蒸馏材料仍可走通用候选流程。实际算子编译与性能验证属于算子工程任务，不用知识摄入成功代替。
3. 所有 producer 共同遵守[质量与证据约束](references/quality-constraints.md)和[路径 Profile](references/frontmatter-profiles.md)。
4. 最后统一更新逐层导航与当天日志，运行全库 lint、重建 Query 索引并执行目标 query。新增或更新卡片不要求构图或关系判定；需要查看链接图谱时再读[本地图谱](references/local-graphs.md)。只读问答不触发这一写入流程。

登记的固定提交本地源码可以按[新来源接入](references/source-onboarding.md)恢复和只读验证；此操作不创建知识卡、不改来源版本，也不触发图谱关系重建。

## 通用建卡

`scripts/knowledge_ingest.py` 负责 `create`、`sync-indexes` 和兼容 CI 的 `build-graph`；它与 `knowledge_graph.py build` 共用同一链接构图实现，不修改 `.gitcode/` 调用约定。构图只读取知识卡链接，不下载或扫描源码，也不属于入库门禁。

先查重并完整读取固定来源。确定 domain、technology/scope 和路径 Profile，再把来源事实、推导结论和待验证假设分开；证据不足时保持 `draft`。

```bash
python3 <skill-dir>/scripts/knowledge_ingest.py --knowledge-root <repo> create \
  --path knowledge/ops/ascendc/apis/example.md \
  --title "标题" --description "可独立理解的摘要" \
  --tag task.lookup --tag topic.data_movement \
  --platform a2 --source <fixed-url> --body-file <body.md> --dry-run
```

审阅 dry-run 后移除 `--dry-run`。`create` 子命令以排他原子写入创建候选卡，不覆盖已有文件，也不更新 index 或日志。默认 `draft`；只有来源、平台、正文与 Profile 门禁均满足后才显式使用 `--status stable`。

Scope 保持可选，不要求每张卡填写或达到填写率。只提取来源支持且有过滤价值的条件；已确认部分即可声明，不等待全部维度齐备，也不为补齐字段写 `any`。先按领域选择已注册 Schema，不把模型推理维度套到其他领域；特殊匹配由受审查的共享 Contract 处理器扩展，卡片不保存可执行规则。卡片声明 Scope 不代表查询已启用过滤，是否过滤以 Query 的显式参数为准。

需要声明场景适用条件时，可用 `--scope-file <JSON/YAML>` 读取 Scope 对象；字段、维度和适用范围由同一 Contract 校验，卡片只用规范值和来源支持的前提。模型推理卡片可声明有来源依据的 `parallelism.none_of`，仍拒绝查询专用的 `model_features.none_of`，不从来源未提及推断否定。参数与 Profile 说明见[路径与 Frontmatter Profile](references/frontmatter-profiles.md)。

## 收尾门禁

- Ingest 的验证由全库确定性命令和仓库 `evals/` 承担，不维护 Skill 内独立测试目录；统一入口仍为根 `bash check.sh`。日常修改仅做必要的定向检查，以下完整收尾流程在提交或推送上库前统一执行，用户明确要求提前全量验证时除外。
- 更新受影响的逐层 `index.md`；可运行 `scripts/knowledge_ingest.py --knowledge-root <repo> sync-indexes` 同步直接子项并保留已有说明及行内/显式引用式导航，再用 `--check` 确认没有陈旧导航。普通卡的人工摘要会保留；卡片标题或 description 改变时，还须核对直接目录条目，不能把同步成功当成摘要已更新。domain 根和 `ops`/`model` 预建 route 保留自己的 index，但不冒充实际覆盖。其他领域不为未来分类提前建空目录。
- 使用系统时间在 `logs/YYYY-MM-DD.md` 顶部记录操作、来源 revision、created/updated/deferred 数和关键裁决。
- Git Reference 批次先生成不可覆盖的 verification receipt；文档归档批次只在日志记录 source ID、来源 URL、本地准备时间和 created/updated/deferred 数。两类批次随后都运行全库 `knowledge-lint`，由外层维护流程按 [Query 索引维护](../knowledge-query/references/cli.md#索引)重建并完整验证索引，再以目标 platform/technology 执行 `knowledge-query`。Query 的只读调用不负责这一步重建。
- 文档归档 API 的头文件字段区分文档显式路径与源码审阅补充；无显式路径时保留同来源的合法补充，不把缺少 `include/` 的归档校验当作源码声明验证。维护与升级边界见[官方 Reference 摄入](references/official-reference-ingest.md)。
- 镜像清理与正文空白例外共用 Contract 的来源角色判定；仅以非主来源引用归档的蒸馏卡不属于过期镜像，不得随同步删除，仍按普通卡片校验。
- Registry 声明 `mirror` 的文档归档 API/Guide 先由获取脚本恢复本地来源树，再使用 `scripts/fixed_archive_docs.py sync --updated-at <UTC>` 重建，并以 `verify` 复验来源树、导航页过滤、声明章节删除、保留正文、链接目标、Frontmatter 与可选的文末导航（普通链接，或「配套 API 与常见组合」小节里同一行不超过 110 字的机制说明）；`index_only` 导航策略不为 README、发布占位、纯链接目录或接口清单建卡，所有目录入口统一使用 `index.md`。配置为省略的“产品支持情况”仍先用于推导并复验 Frontmatter `platforms`，随后才从正文删除。官方归档持续更新，不校验归档或内容树 SHA-256；获取脚本只对已知文件中的特定 token 执行幂等的发布器链接修复，不固定次数，未知代码损坏仍报错。没有产品支持表、能力枚举或明确限定整张卡片/本接口范围的“仅支持/仅针对…生效”等证据时不得自动写为 `agnostic`，必须使用 `draft` 与空平台范围，章节内局部能力限制不能提升为整卡平台。API 引用建议按需使用 `scripts/api_operator_links.py suggest`，只生成 ignored 报告，不回写卡片或作为入库门禁；采用的引用使用普通 Markdown 链接。已有来源的等价本地化和资源恢复见[新来源接入](references/source-onboarding.md)，不作为新 Git Reference 批次重建 inventory/ledger，不改技术断言。
- 普通知识卡链接按技术叙述需要添加；不要求每张卡都有链接，不额外生产图谱关系。

## 边界

- 不自动 commit、push、提 PR 或发布 Skill。
- 对独立知识根只执行本 Skill 自带的 Contract；目标根 Contract 与当前版本不一致时失败，不导入目标根 Python。
- 更新前完整读取原卡并做增量融合；除 Registry 文档归档的官方 API/Guide 受控转换外，不整体覆盖或机械复制上游文件。文档归档只选择含独立技术事实的页面；保留正文只能删除 Registry 声明的冗余章节并改写因入库路径变化或导航页过滤而失效的链接目标。可以在保留的来源正文之后添加普通知识卡链接，或按 AGENTS.md 的边界追加「配套 API 与常见组合」小节。图谱与 API 引用建议只写入 ignored 的 `artifacts/graphs/`，不回写知识卡。
- 不把固定来源、脚本成功或 lint 通过等同于人工复核。
- 未迁移 producer 必须 defer；不要用通用建卡脚本声称完成其专用语义分析。
