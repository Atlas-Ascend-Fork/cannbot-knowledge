# 本地图谱

关系构建遵循“代码宽召回、Agent 语义判定、代码确定性聚合”的边界。词项、tags、路径和分数只能减少明显无效的阅读量，不能代替 Agent 判断关系是否成立。

`<skill-dir>` 是 `knowledge-ingest/SKILL.md` 所在目录；所有命令显式传入 `<repo>`。

## 全量流程

```bash
python3 <skill-dir>/scripts/knowledge_graph.py --knowledge-root <repo> candidates
python3 <skill-dir>/scripts/knowledge_graph.py --knowledge-root <repo> make-shards --count 90
```

`candidates` 的 `--limit` 默认从每张 focal 选取 30 个词法候选，再与其他 focal 的反向入选候选取无向并集，并补入正文显式技术符号、本地人工链接和小型文档 bundle 的 sibling。正文符号、API 拼写片段、标题、摘要、aliases、路径和高信息 tags 只形成多个宽召回通道；最终候选数可以高于 30。它只排除自环、重复、无效端点和没有任何召回信号的配对，不按 CANN 版本、平台、标题强词、分数阈值或节点度数判定关系。

`make-shards` 把所有 focal 稳定写入 ignored 的 `artifacts/graphs/judgment_shards/`。分片数量按语料规模和可用 subagent 调整；一个分片宜包含约 20–40 张 focal。每个 packet 带双方路径、内容指纹、摘要、正文 excerpt、来源和 recall hints，subagent 仍必须打开实际文件阅读全文。

至少使用两个独立 subagent 分担全量 focal。每个 subagent 对其分片执行：

1. 阅读 focal 完整人工正文，提取任务、现象、机制/根因、方案或接口契约、适用边界、验证和来源；加载器会排除 `cannbot:related` 受管区块，避免派生导航反过来影响候选、指纹和判定。
2. 浏览全部候选摘要形成 shortlist，再完整读取 shortlist 双方正文和可用来源。候选分数和共享词只用于定位，不构成接受理由。
3. 只有当从 focal 导航到 candidate 能实质推进理解、使用、排障或验证同一任务链时保留；仅共享目录、平台、错误码、API 名、流水名或 tag 不足以成边。
4. 普通目录归属、总览列出成员或同 bundle sibling 已由 `part_of` 与人工导航表达，不重复生成 semantic edge；只有总览额外提供该成员必需的选型、调用或约束信息时才保留。
5. 理由必须说明双方任务、机制、接口契约、根因/修复或验证怎样衔接，不写“共享某词、可交叉核对、共同组成闭环”模板。
6. 候选是减少无效阅读的 shortlist，不是封闭边界。若 focal 正文明示一个未召回但确实相关的现有卡，subagent 可在 decision 中增加 `agent_discovered: true` 和该卡当前 `target_fingerprint`；聚合器会校验端点与指纹，但不替 Agent 判断关系。后续定向语义审计补入的 decision 可用可选 `judge` 记录实际作出该项判断的 Agent；未提供时继承 review 顶层 `judge`。
7. 每个 focal 必须返回一个 result，即使 `kept` 为空；不能遗漏难判断的 focal。争议项先放入 `needs_adjudication`，交另一个 subagent 阅读双方全文裁决后再清空。

review 文件格式如下：

```json
{
  "schema_version": 2,
  "shard_id": "shard-000",
  "shard_fingerprint": "<packet 中的值>",
  "judge": "subagent:<id>",
  "results": [
    {
      "focal_id": "ops/ascendc/runbooks/compilation/example",
      "candidate_set_fingerprint": "<packet 中 focal 的值>",
      "kept": [
        {
          "target_id": "ops/ascendc/apis/example",
          "relation": "exemplifies",
          "reason": "该 Runbook 的失败由接口参数边界触发，API 卡给出修复所需的参数契约。",
          "confidence": "high",
          "strength": "direct",
          "evidence": {
            "bridge": "Runbook 根因与 API 参数约束直接对应",
            "scope_note": "双方平台范围一致"
          }
        }
      ],
      "needs_adjudication": []
    }
  ]
}
```

全部分片完成后一次性聚合并收尾：

```bash
python3 <skill-dir>/scripts/knowledge_graph.py --knowledge-root <repo> aggregate \
  --input <review-000.json> --input <review-001.json>
python3 <skill-dir>/scripts/knowledge_graph.py --knowledge-root <repo> finalize
```

`aggregate` 要求至少两个不同的 subagent 覆盖 manifest 中每个 shard 和每张 focal，校验 shard、候选集合和双方卡片指纹，并拒绝未明确声明或指纹不匹配的候选外发现、空理由、非法关系和未裁决项。它从空集合聚合 Agent 结果，不使用确定性关系基线，也没有图谱 degree 上限。

如果两个 review 都接受同一 pair 但对 `same_topic`/`related` 分类不一致，`aggregate` 会生成 `artifacts/graphs/adjudication/conflicts.json` 并失败关闭。可以把该 packet 拆给多个 subagent 并行阅读每组双方完整正文；每个裁决分片都带相同 `conflict_fingerprint`、自己的 `judge` 和互不重叠的逐 pair `decisions`。聚合时重复传入 `--adjudication`，所有分片的并集必须恰好覆盖全部冲突：

```bash
python3 <skill-dir>/scripts/knowledge_graph.py --knowledge-root <repo> aggregate \
  --input <review-000.json> --input <review-001.json> \
  --adjudication <agent-adjudication-part-0.json> \
  --adjudication <agent-adjudication-part-1.json>
```

`aggregate` 把接受关系、卡片指纹、理由、Agent 身份、强度、置信度和证据写入 ignored 的 `artifacts/graphs/edge_judgments.json`，不改写知识卡。`finalize` 使用该本地缓存同步卡片中可提交的 `cannbot:related` 受管导航块，再在 ignored 目录合成 JSON、生成 HTML 可视化并校验缓存、图谱和关系块一致。

## 关系语义

- `Runbook → API` 规范为 `exemplifies`，表示实践问题直接依赖接口契约。
- `Guide → API` 规范为 `explains`，表示指南实质解释接口或其使用边界。
- 同 Profile 由 subagent 在 `same_topic` 与 `related` 中选择；前者要求主题和决策核心一致，后者表示有明确任务链衔接但并非同一主题。
- 其他跨 Profile 规范为 `related`。方向和关系枚举由聚合器机械归一化，但关联是否成立只能由 subagent 判断。
- `part_of` 从目录和逐层 Index 派生；`links_to` 只来自人工正文，解析时排除旧版本可能残留的受管区块。

候选不是边，Agent 接受的关系只是导航和交叉核对线索。技术回答仍必须打开人工正文并核对来源，Query 不索引受管关系块。候选、分片、review、冲突、判定缓存、完整图谱和可视化都位于 `artifacts/graphs/`，始终 gitignore；只有知识卡内由其派生的 `cannbot:related` 导航块进入 Git。克隆仓库可以消费这些导航，但没有本地判定缓存；需要重建或更新时必须重新执行完整多 Agent 流程。

使用 `related <Concept-ID>` 查看单卡关系，使用 `explain <left-ID> <right-ID>` 查看判定理由、Agent、强度、置信度和证据。
