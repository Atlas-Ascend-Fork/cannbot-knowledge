---
name: knowledge-ingest
description: 将所有 cannbot-knowledge 摄入请求统一路由，并把官方文档、固定版本源码或人工材料蒸馏为符合 OKF v0.2 与 CANNBot Profile 的候选卡。接入 Git 或固定归档来源、按 commit 增量同步、升级来源版本、创建或更新知识、整理错误经验，或执行关系候选召回、判定聚合、关系块注入、本地图谱合成和校验时使用；当前内置通用建卡、官方 Reference 和本地图谱完整流程，未接入 producer 明确 defer。
---

# Knowledge Ingest

本 Skill 是通用摄入路由入口。先判断变化类型和来源类型，再执行已接入 producer；用户也可按 `ops-knowledge-trace-ingest` 的手动触发词在本知识仓直接启动 trace producer。两种入口都不得绕过各 producer 的证据和收尾门禁。

## 路由

1. 判断来源与生命周期：首次接入读[新来源接入](references/source-onboarding.md)；Git 同 ref 推进读[增量同步](references/incremental-sync.md)，Git ref/大版本切换读[版本升级](references/version-upgrade.md)；Registry 登记的固定归档执行官方 Reference 中的直接流程，不调用 Git inventory 工具。
2. 判断 producer：
   - 官方文档、技术 reference、固定版本源码说明：执行[官方 Reference 摄入](references/official-reference-ingest.md)。
   - 已经蒸馏好的人工材料或单张候选：使用本 Skill 的 `create` 流程。
   - 算子开发 trace、会话日志或已归一化事件流：在本知识仓路由到 [`ops-knowledge-trace-ingest`](../ops-knowledge-trace-ingest/SKILL.md)；业务项目的 contributor 安装不携带该仓内 producer，此时记录 `defer` 并说明需在独立知识仓执行。
   - 完整样例分析、VV/CV 算子编译、Issue/PR 证据编译：当前尚未迁移，记录 `defer` 原因并等待对应 producer 完成架构评审后接入。
3. 所有 producer 共同遵守[质量与证据约束](references/quality-constraints.md)和[路径 Profile](references/frontmatter-profiles.md)。
4. 最后统一更新逐层导航与当天日志，按[本地图谱](references/local-graphs.md)执行宽候选召回，并把稳定分片交给多个独立 subagent 阅读全文判定；聚合完成后同步知识卡的受管关系块，并在 ignored 的 `artifacts/graphs/` 合成、可视化和校验本地图谱，最后运行全库 lint、重建 Query 索引并执行目标 query。只读问答不触发这一写入流程。

## 通用建卡

先查重并完整读取固定来源。确定 domain、technology/scope 和路径 Profile，再把来源事实、推导结论和待验证假设分开；证据不足时保持 `draft`。

```bash
python3 <skill-dir>/scripts/knowledge_ingest.py --knowledge-root <repo> create \
  --path knowledge/ops/ascendc/apis/example.md \
  --title "标题" --description "可独立理解的摘要" \
  --tag task.lookup --tag topic.data_movement \
  --platform a2 --source <fixed-url> --body-file <body.md> --dry-run
```

审阅 dry-run 后移除 `--dry-run`。`create` 子命令以排他原子写入创建候选卡，不覆盖已有文件，也不更新 index 或日志。默认 `draft`；只有来源、平台、正文与 Profile 门禁均满足后才显式使用 `--status stable`。

## 收尾门禁

- 更新目标目录到 Bundle 根的全部 `index.md`；可运行 `scripts/knowledge_ingest.py --knowledge-root <repo> sync-indexes` 同步直接子项并保留已有说明及行内/显式引用式导航，再用 `--check` 确认没有陈旧导航。domain 根和 `ops`/`model` 预建 route 保留自己的 index，但不冒充实际覆盖。其他领域不为未来分类提前建空目录。
- 使用系统时间在 `logs/YYYY-MM-DD.md` 顶部记录操作、来源 revision、created/updated/deferred 数和关键裁决。
- Git Reference 批次先生成不可覆盖的 verification receipt；固定归档批次只在日志记录 source ID、归档 SHA-256 和 created/updated/deferred 数。两类批次随后都运行全库 `knowledge-lint`，并以目标 platform/technology 执行 `knowledge-query`。
- 图谱没有确定性 judge 或自动 `full` 捷径。全量重建先用 `reset` 清除 ignored 的旧产物，再依次运行 `candidates`、`make-shards`，由多个 subagent 以每次一至两个 shard 的小批次覆盖全部 focal，主 Agent 使用 `aggregate` 聚合全部 review，再运行 `finalize`。每个接受或显式拒绝的双端 anchor 必须逐字存在于对应卡片的非受管正文。召回分数只帮助定位候选，不决定是否成边；不得用规则输出冒充 Agent 语义判定。接受/显式拒绝冲突和关系类型冲突必须交给未参与对应 pair 原判定的 subagent 裁决，裁决分片必须互不重叠且合并后恰好覆盖完整冲突集；聚合失败会使旧缓存失效，语料或候选产物变化后也拒绝复用缓存。

## 边界

- 不自动 commit、push、提 PR 或发布 Skill。
- 对独立知识根只执行本 Skill 自带的 Contract；目标根 Contract 与当前版本不一致时失败，不导入目标根 Python。
- 更新前完整读取原卡并做增量融合；不整体覆盖，不按上游文件一对一复制知识卡。图谱流程只能改写 `cannbot:related` 受管区块，不得改动其他正文；关系目标渲染为导航链接，Agent 理由只渲染为去活化链接语法后的单行纯文本，不能把理由中引用的 Markdown 变成新的人工链接。这些区块作为卡片导航提交，候选、review、冲突裁决、判定缓存、JSON 和 HTML 则都只保存在 ignored 的 `artifacts/graphs/`，不得提交。
- 不把固定来源、脚本成功或 lint 通过等同于人工复核。
- 未迁移 producer 必须 defer；不要用通用建卡脚本声称完成其专用语义分析。
