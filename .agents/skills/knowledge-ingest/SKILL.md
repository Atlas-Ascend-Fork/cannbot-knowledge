---
name: knowledge-ingest
description: 将所有 cannbot-knowledge 摄入请求统一路由，并把官方文档、固定版本源码或人工材料蒸馏为符合 OKF v0.2 与 CANNBot Profile 的候选卡。接入 Git 或固定归档来源、按 commit 增量同步、升级来源版本、创建或更新知识、整理错误经验或重建本地图谱时使用；当前内置通用建卡、Git Reference 批次和固定归档直接摄入流程，未迁移 producer 明确 defer。
---

# Knowledge Ingest

本 Skill 是唯一摄入入口。先判断变化类型和来源类型，再执行已接入 producer；不要绕过路由直接调用内部脚本。

## 路由

1. 判断来源与生命周期：首次接入读[新来源接入](references/source-onboarding.md)；Git 同 ref 推进读[增量同步](references/incremental-sync.md)，Git ref/大版本切换读[版本升级](references/version-upgrade.md)；Registry 登记的固定归档执行官方 Reference 中的直接流程，不调用 Git inventory 工具。
2. 判断 producer：
   - 官方文档、技术 reference、固定版本源码说明：执行[官方 Reference 摄入](references/official-reference-ingest.md)。
   - 已经蒸馏好的人工材料或单张候选：使用本 Skill 的 `create` 流程。
   - 完整样例分析、VV/CV 算子编译、开发轨迹进化、Issue/PR 证据编译：当前尚未迁移，记录 `defer` 原因并等待对应 producer 通过后续 PR 接入。
3. 所有 producer 共同遵守[质量与证据约束](references/quality-constraints.md)和[路径 Profile](references/frontmatter-profiles.md)。
4. 最后统一更新逐层导航与当天日志，运行全库 lint、目标 query，并按需重建[本地图谱](references/local-graphs.md)。

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
- 需要关系视图时运行 `knowledge_ingest.py --knowledge-root <repo> build-graph`；产物只写 ignored 的 `artifacts/graphs/`。

## 边界

- 不自动 commit、push、提 PR 或发布 Skill。
- 对独立知识根只执行本 Skill 自带的 Contract；目标根 Contract 与当前版本不一致时失败，不导入目标根 Python。
- 更新前完整读取原卡并做增量融合；不整体覆盖，不按上游文件一对一复制知识卡。
- 不把固定来源、脚本成功或 lint 通过等同于人工复核。
- 未迁移 producer 必须 defer；不要用通用建卡脚本声称完成其专用语义分析。
