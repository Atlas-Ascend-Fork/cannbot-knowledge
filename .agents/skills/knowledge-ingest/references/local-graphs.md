# 本地图谱

关系构建遵循“代码宽召回、Agent 语义判定、代码确定性聚合”的边界。词项、tags、路径和分数只能减少明显无效的阅读量，不能代替 Agent 判断关系是否成立。

`<skill-dir>` 是 `knowledge-ingest/SKILL.md` 所在目录；所有命令显式传入 `<repo>`。

## 全量流程

```bash
python3 <skill-dir>/scripts/knowledge_graph.py --knowledge-root <repo> reset
python3 <skill-dir>/scripts/knowledge_graph.py --knowledge-root <repo> candidates
python3 <skill-dir>/scripts/knowledge_graph.py --knowledge-root <repo> make-shards --count 90
```

`reset` 只删除 ignored 的 `artifacts/graphs/` 可重建产物，用于全量重建前排除旧 review、裁决和缓存混入；不会修改知识卡或 `.gitcode/`。增量诊断不需要执行它。

`candidates` 的 `--limit` 默认从每张 focal 选取 30 个词法候选，再与其他 focal 的反向入选候选取无向并集，并补入正文显式技术符号、本地人工链接和小型文档 bundle 的 sibling。正文符号、API 拼写片段、标题、摘要、aliases、路径和高信息 tags 只形成多个宽召回通道；最终候选数可以高于 30。它只排除自环、重复、无效端点和没有任何召回信号的配对，不按 CANN 版本、平台、标题强词、分数阈值或节点度数判定关系。

`make-shards` 把所有 focal 稳定写入 ignored 的 `artifacts/graphs/judgment_shards/`。分片数量按语料规模和可用 subagent 调整；一个分片宜包含约 20–40 张 focal。每个 packet 带双方路径、内容指纹、摘要、正文 excerpt、来源和 recall hints，subagent 仍必须打开实际文件阅读全文。

至少使用两个独立 subagent 分担全量 focal。单次委派以一个 shard 为宜、不得超过两个 shard；完成并核对该批输出后才能继续委派，不能把数十个 shard 交给一次批量模板生成。每个 subagent 对其分片执行：

1. 阅读 focal 完整人工正文，提取任务、现象、机制/根因、方案或接口契约、适用边界、验证和来源；加载器会排除 `cannbot:related` 受管区块，避免派生导航反过来影响候选、指纹和判定。
2. 浏览全部候选摘要形成 shortlist，再完整读取 shortlist 双方正文和可用来源。候选分数和共享词只用于定位，不构成接受理由。
3. 只有当从 focal 导航到 candidate 能实质推进理解、使用、排障或验证同一任务链时保留；仅共享目录、平台、错误码、API 名、流水名或 tag 不足以成边。
4. 普通目录归属、总览列出成员或同 bundle sibling 已由 `part_of` 与人工导航表达，不重复生成 semantic edge；只有总览额外提供该成员必需的选型、调用或约束信息时才保留。
5. 理由必须说明双方任务、机制、接口契约、根因/修复或验证怎样衔接，不写“共享某词、可交叉核对、共同组成闭环”模板，不提交尾部省略号截断的摘录，也不能把“不覆盖”“不适用”等否定边界反向当作正向关系证据。`evidence.anchors` 必须以双方 Concept ID 为键，分别从去除受管关系块后的对应卡片正文逐字摘录一项具体事实；正文内的合法模板或 shape 省略符可保留，但不得用召回包的截断 excerpt 代替全文证据。`bridge` 必须逐字包含两个 anchor 并说明衔接，`scope_note` 说明成立或拒绝的范围。
6. 候选是减少无效阅读的 shortlist，不是封闭边界。若 focal 正文明示一个未召回但确实相关的现有卡，subagent 可在 decision 中增加 `agent_discovered: true` 和该卡当前 `target_fingerprint`；聚合器会校验端点与指纹，但不替 Agent 判断关系。后续定向语义审计补入的 decision 可用可选 `judge` 记录实际作出该项判断的 Agent；未提供时继承 review 顶层 `judge`。
7. 每个 focal 必须返回一个 result，即使 `kept` 为空；不能遗漏难判断的 focal。未出现在 `kept` 或 `rejected` 中表示 abstain，不能推断为否决。只有完整阅读双方正文并确认候选是容易误接的近似项时才写入 `rejected`，并提供与接受关系同样完整的双端证据。
8. `keep` 与显式 `rejected` 冲突、同一 pair 的关系类型冲突，以及 `needs_adjudication` 中的争议，都必须交给未参与该 pair 原判定的独立 subagent 阅读双方全文裁决。聚合失败会使旧判定缓存失效，不能在裁决前继续 `finalize`。

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
          "reason": "Runbook 观测到第四个 pad 参数触发编译失败；该失败由 API 卡声明 UB→GM 方向仅存在三参数重载解释。",
          "confidence": "high",
          "strength": "direct",
          "evidence": {
            "anchors": {
              "ops/ascendc/runbooks/compilation/example": "Runbook 观测到第四个 pad 参数触发编译失败",
              "ops/ascendc/apis/example": "API 卡声明 UB→GM 方向仅存在三参数重载"
            },
            "bridge": "Runbook 观测到第四个 pad 参数触发编译失败；该失败由 API 卡声明 UB→GM 方向仅存在三参数重载解释。",
            "scope_note": "仅适用于 UB→GM 方向的该重载，不泛化到 DataCopy 或其他搬运方向"
          }
        }
      ],
      "rejected": [],
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

`aggregate` 要求至少两个不同的 subagent 覆盖 manifest 中每个 shard 和每张 focal，校验 shard、候选集合和双方卡片指纹，并拒绝未明确声明或指纹不匹配的候选外发现、模板或截断理由、不在对应卡片正文中的双端 anchor、非法关系和未裁决项。它从空集合聚合 Agent 结果，不使用确定性关系基线，也没有图谱 degree 上限。每次聚合开始时先使旧判定缓存失效，失败后无法继续使用同语料的旧缓存。

如果 review 对同一 pair 同时存在接受和显式拒绝，或两个接受判定对 `same_topic`/`related` 分类不一致，`aggregate` 会生成 `artifacts/graphs/adjudication/conflicts.json` 并失败关闭。可以把该 packet 拆给多个未参与对应 pair 原判定的 subagent 并行阅读每组双方完整正文；每个裁决分片都带相同 `conflict_fingerprint`、自己的 `judge` 和互不重叠的逐 pair `decisions`，每项用 `accept: true|false` 明确决定关系是否成立。聚合时重复传入 `--adjudication`，所有分片的并集必须恰好覆盖全部冲突：

```bash
python3 <skill-dir>/scripts/knowledge_graph.py --knowledge-root <repo> aggregate \
  --input <review-000.json> --input <review-001.json> \
  --adjudication <agent-adjudication-part-0.json> \
  --adjudication <agent-adjudication-part-1.json>
```

`aggregate` 把接受关系、卡片指纹、候选产物指纹、理由、Agent 身份、强度、置信度和证据写入 ignored 的 `artifacts/graphs/edge_judgments.json`，不改写知识卡。显式拒绝只保留在 ignored 的 review/裁决审计产物中，不进入图谱。`finalize` 会重新核对当前语料和候选产物指纹；任一变化都失败关闭。校验通过后，它先用该缓存在 ignored 目录合成 JSON 和 HTML，确认缓存与产物可生成后才同步知识卡中可提交的 `cannbot:related` 受管导航块，最后校验缓存、图谱、HTML 和关系块一致。

受管关系块只把目标卡标题渲染为导航链接；Agent 理由按单行纯文本渲染。理由中从任一端正文引用的 Markdown 链接语法必须去活化，不能让其按关系块所在卡片的目录重新解析为人工链接或产生断链。

## 关系语义

- `Runbook → API` 规范为 `exemplifies`，表示实践问题直接依赖接口契约。
- `Guide → API` 规范为 `explains`，表示指南实质解释接口或其使用边界。
- 同 Profile 由 subagent 在 `same_topic` 与 `related` 中选择；前者要求主题和决策核心一致，后者表示有明确任务链衔接但并非同一主题。
- 其他跨 Profile 规范为 `related`。方向和关系枚举由聚合器机械归一化，但关联是否成立只能由 subagent 判断。
- `part_of` 从目录和逐层 Index 派生；`links_to` 只来自人工正文，解析时排除旧版本可能残留的受管区块。

候选不是边，Agent 接受的关系只是导航和交叉核对线索。技术回答仍必须打开人工正文并核对来源，Query 不索引受管关系块。候选、分片、review、冲突、判定缓存、完整图谱和可视化都位于 `artifacts/graphs/`，始终 gitignore；只有知识卡内由其派生的 `cannbot:related` 导航块进入 Git。克隆仓库可以消费这些导航，但没有本地判定缓存；需要重建或更新时必须重新执行完整多 Agent 流程。

使用 `related <Concept-ID>` 查看单卡关系，使用 `explain <left-ID> <right-ID>` 查看判定理由、Agent、强度、置信度和证据。
