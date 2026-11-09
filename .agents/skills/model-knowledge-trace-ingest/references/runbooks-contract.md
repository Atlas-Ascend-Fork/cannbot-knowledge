# 模型证据与策展合同

本合同由使用 Skill 的执行 Agent 填写，脚本仅验证本地证据、映射和字节；不定义模型响应协议或客户端调度。

## 提取标准

候选要同时满足模型/框架执行场景相关、非显然、可复用以及本轨迹内有客观证据。一个独立因果或诊断规则一张卡；同根因多轮调参合并，不按轮次拆卡。以下形态的必要角色不同：

| knowledge_form（仅账本） | evidence_roles 必要键 | 判定 |
|---|---|---|
| repair_recipe | failure、before、after、validation | 失败、完整修改单元、修后客观验证闭合 |
| diagnostic_rule | trigger、probe、observation、discrimination | 有触发、可执行探针、客观观测与能区分的分支 |
| negative_result | attempt、failure、boundary | 尝试客观失败/回退，明确失败条件，不伪称成功 |
| validated_pattern | implementation、validation | 完整实现/配置单元，且轨迹中完成相应验证 |

角色值是事件锚点列表，每项为 `{source: 0, sequence: 12}`；source 指向账本 entry 的 `sources` 数组。工具输出优先于消息叙述，`tool_observed` 才能直接作为信号；`artifact_verified` 还要求信号绑定到核验过的源码/产物。退出码 0 不自动代表精度或性能正确。

`evidence_audit.trace_snapshot` 只使用模型合同需要的内容，不从其他领域的事件形态推导模型证据。每个 adopted claim 有非空结论、关联事件和客观 signals；正文不能新增未进入 claim mapping 的事实。代码/配置 artifact 要给出完整机制单元（函数、配置段、启动参数或诊断命令），逐字出现在脱敏事件及最终卡中；多个 edit 片段须先补齐重建证据，不能凭空拼完整实现。

性能改善类结论要有 `performance_comparison`：baseline/candidate 各含 workload 与 metric 字段及客观事件锚点。两者的 `model`、`hardware`、`precision`、`input_tokens`、`output_tokens`、`batch_or_concurrency`、`parallelism`、`measurement` 必须相同且非 unknown；metric 的 name/unit/aggregation 相同，value 为有限数字。还需审查 warmup、同步、重复次数、统计与精度基线。框架版本/代码变化应写明；多项变量同时变化不能单点归因。字段一致只证明结构可比，审查者仍须从事件确认这些条件。

测量错误本身可形成 diagnostic_rule 或 negative_result，而不能把重定义计时范围称为模型加速。服务、单 batch、单 kernel 指标不能互换；单次延时不外推普遍收益。

## 暂存账本

同一 ledger 只处理一个 route；最终卡相对 staged 根的路径为 `<area>/<slug>.md`。`status: published`/`merged` 表示计划采纳，在真正发布和检查前不能报告已入库；其他条目为 `deferred`/`rejected`，必须有 reason。

策展时提供挖掘阶段的 `model.trace-mining.v1` 候选 manifest，并在 ledger 记录 `candidates_manifest_sha256`。每个 entry 的 `source_candidate_ids` 列出其处理的输入候选；省略时只表示 entry.candidate_id 自身。合并条目保留所有成员，拒绝/暂缓条目也占对应候选；每个 route 的输入候选必须恰好覆盖一次。校验器的 `--candidates-manifest` 同时核对实际 hash 和覆盖，审查 subject 再绑定 ledger 的该 hash。

```json
{
  "schema_version": "model.trace-ledger.v1",
  "curation_contract": "model.trace-curation.v1",
  "route": "inference",
  "reconstruction_sha256": "同目录 reconstruction.json 的实际 SHA-256",
  "candidates_manifest_sha256": "挖掘 manifest.json 的实际 SHA-256",
  "entries": [{
    "candidate_id": "candidate-1",
    "source_candidate_ids": ["candidate-1"],
    "status": "published",
    "operation": "new",
    "target_path": "runtime/example_slug.md",
    "knowledge_form": "diagnostic_rule",
    "reproduce_count": 1,
    "scope_evidence": {"summary": "实际模型或框架任务及本机制与它的关系", "anchors": [{"source": 0, "sequence": 1}]},
    "validation_scope": ["source_read"],
    "dedup": {"decision": "create", "queries": ["实际执行的 query"], "read_paths": []},
    "sources": [{
      "normalized_dir": "实际归一化目录的绝对路径",
      "raw_source_sha256": "session_manifest.source.sha256",
      "normalized_trace_sha256": "normalized_trace.jsonl 的 SHA-256"
    }],
    "evidence_roles": {
      "trigger": [{"source": 0, "sequence": 1}],
      "probe": [{"source": 0, "sequence": 2}],
      "observation": [{"source": 0, "sequence": 3}],
      "discrimination": [{"source": 0, "sequence": 4}]
    },
    "claims": [{
      "id": "claim-1", "text": "候选结论原文",
      "anchors": [{"source": 0, "sequence": 3}],
      "signals": [{"source": 0, "sequence": 3}]
    }],
    "evidence_audit": {
      "result": "pending", "mode": "trace_snapshot",
      "trace_snapshot": {"mechanism_artifacts": [{
        "claim_ids": ["claim-1"], "text": "逐字代码或配置",
        "anchors": [{"source": 0, "sequence": 2}],
        "verbatim_verified": false
      }]}
    }
  }]
}
```

update/merge 使用 `status: merged`、`operation: merge`，并记录 `expected_target_sha256` 作为覆盖前置条件。reproduce_count 不得大于已核验不同 raw_source_sha256 数；不同原始内容也不自动构成独立实验，独立性由审查判断。未采纳项不需要伪造 sources，但必须记录原因。

### 策展保真与断言去向

新策展使用 `curation_contract: model.trace-curation.v1`，强制绑定原候选 manifest。旧账本仍可校验；附带原 manifest 时同样检查信息保留，缺失绑定的旧账本不能宣称经过新合同验证。

- 逐条保留原 claim 的 text、kind、其他语义字段及锚点绑定；性能改善的 kind 为 `performance_gain`，不能删去类型以绕过比较。原 `performance_comparison` 无论是否标 gain 都完整保留。
- 删减 claim 用 `claim_dispositions: [{candidate_id, claim_id, action: "omitted", reason}]` 显式记账，并移除标题、摘要、正文中的对应断言。脚本检查原文残留；改写后的等价断言仍须审查者识别。全部不采纳时 defer/reject，不能伪造剩余 claim。
- 原 artifact 支撑仍采用的 claim 时保留完整 text；不能用匹配子串替换。单元本身不完整或结论需改写时，保留旧挖掘记录，明确形成新候选修订与新 hash，重做查重/验证/审查；修改 manifest 不能充当自动证实。
- 多个候选合并为一张卡时，各 claim 用 `source_claims: [{candidate_id, claim_id}]` 指回原成员。可重命名本卡 claim id 并显式重排来源锚点，但不能改变其绑定的事件或正文结论。每个成员的性能对比放在 `performance_comparisons: {"原candidate_id": {"baseline": {}, "candidate": {}}}`；不能与单数 performance_comparison 混用。每对均按同一性能合同验证，不把成员甲的基线配给成员乙。合并需执行 Agent 显式处理，不由策展脚本自动重写。
- `scope_evidence` 包含实际任务关系 summary 和原文 anchors；`validation_scope` 为非空数组，取 source_read/static_check/cpu_reference/device_functional/end_to_end/performance，列出实际完成的验证。字段合法不等于该层次真实完成，仍须审查。

标题、摘要和六节正文均属于待审断言面。claim 文本包含于正文和原文逐字匹配只证明机械对应，不能证明 API 语义、因果、完整实现或性能收益。相关检查由 [reviewer.md](reviewer.md) 的逐卡覆盖闭环，不能用哈希一致代替语义审查。

reconstruction 使用 `model.trace-reconstruction.v1`、对应 `route` 及逐来源 `traces`。每个 trace 的 `source` 与 ledger 的来源项完全相同，并记录 `task.summary`、`environment`（模型与框架、平台/版本）、`timeline`、`facts`、`assumptions`、`unknowns`、`limitations` 和 `coverage`。timeline/facts 各条提供本来源的 `event_refs` 整数数组，区分实际启动、日志结果、源码快照与 Agent 自述。coverage 的 `indexed_sequence_range: [1,N]` 表示确定性索引覆盖，`semantic_review_ranges: [[start,end],...]` 单独声明实际语义审查范围，不能将索引覆盖谎报为全轨迹语义提取完成。

同一来源中的多次实验分别重建，不能因文件相邻就串成同一个闭环；源码读取时间、源码修改时间与日志运行时间未对齐时，不能用当前源码解释历史 verdict。ledger 记录 reconstruction 的实际 SHA-256，校验和 receipt 同时绑定其内容。私有路径与 raw/normalized 溯源留在账本；公开卡不粘贴整段聊天、账号标识或凭据。

## 正文

Frontmatter 使用 Runbook Profile 的当前必选字段；新候选默认 draft，明确平台和完整证据且经审查后才能 stable。可用 `sources: []`；不为轨迹创建假的公开 URL，不因入库自动增加 `verified`。

正文包含一个 H1，并按实际知识形态组织：

- `## 适用场景`：模型/框架、平台/版本、目标与工作负载；缺失信息明确说明。
- `## 触发与观测`：故障或优化目标，以及逐字客观输出。
- `## 探针与操作`：完整代码/配置/命令及必要 before/after；失败路线明确不可采用。
- `## 机制与判别`：一个结论对应的证据、可区分解释和未验证推断。
- `## 验证信号`：只列本 trace 内真正观测到的信号，注明平台与证据等级；单次观测标明单次，收益带条件、单位与基线。
- `## 适用与失效边界`：模型/框架版本、并行/量化条件、可能不成立的情况及停止/回退条件。

不确定机制可以作为假设写入边界，但不能在前文宣称已经证实。后续验证建议与已完成观测明确分开。

## 多轨迹批次绑定

多轨迹输入使用 [batch-processing.md](batch-processing.md) 的输入批清单和批级去向。curate ledger可增加私有batch_manifest对象（绝对path及sha256）；证据校验器在存在该绑定时核对源成员及source_family复现上限。该字段不进入知识卡frontmatter，旧单来源账本保持兼容。批包/窗口提供的是原文数据，不自动授予语义覆盖、verbatim批准或独立审查通过。
