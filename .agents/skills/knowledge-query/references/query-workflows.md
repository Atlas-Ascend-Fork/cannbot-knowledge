# 查询与证据工作流

复杂任务使用本文件，将检索召回和工程判断分开。

## 审计查询

1. 建立目标边界：实体、platform、CANN version、工程形态、dtype/layout、workload 和验证边界。
2. 列出 decisions；每个 decision 只回答一个判断，例如参数单位、错误信号是否有已验证修复、性能瓶颈的主导机制。
3. 为每个 decision 运行窄查询，保存独立 receipt。互不依赖的 decision 可以并行，但 receipt 路径不能复用。
4. 选择性读取少量候选卡和固定来源，只记录来源事实、适用边界、negative evidence、conflict 和 gap。
5. 主任务将 decision 标为 `covered`、`conflicting`、`insufficient` 或 `gap`。只对未解决项补搜；补搜应从实体转向错误信号、从机制转向 API 契约或从现象转向验证过的修复路径。
6. 无新增证据或达到预算时停止。把 target、decision、receipt 和采用的卡片路径/指纹冻结为 `cannbot-retrieval-state.v1`；全部 covered 后运行 `retrieval_state.py --require-ready --receipt`。生成的 ready receipt 会绑定全部 search receipt 的 SHA-256。
7. 实现后的正确性、性能和平台实验写入 `cannbot-retrieval-outcome.v1`，绑定 state、ready receipt 和真实产物 SHA-256，再运行 `retrieval_outcome.py --require-complete --receipt`。不得修改原始 search receipt；任何改动都会使 outcome 链失效。

最小 state：

```json
{
  "schema_version": "cannbot-retrieval-state.v1",
  "target": {"entity": "DataCopyPad", "platforms": ["a2"]},
  "decisions": [{
    "id": "api-contract",
    "question": "目标接口契约是什么？",
    "status": "covered",
    "receipts": ["/absolute/search.json"],
    "evidence": [{"path": "ops/ascendc/apis/example", "card_sha256": "<sha256>"}]
  }]
}
```

最小 outcome manifest：

```json
{
  "schema_version": "cannbot-retrieval-outcome.v1",
  "state": "/absolute/retrieval_state.json",
  "state_sha256": "<sha256>",
  "ready_receipt": "/absolute/retrieval_ready.json",
  "ready_receipt_sha256": "<sha256>",
  "events": [{
    "decision": "api-contract",
    "outcome": "verified",
    "summary": "目标平台验证通过",
    "observed": ["correctness passed"],
    "artifacts": [{"path": "/absolute/test.log", "sha256": "<sha256>"}]
  }]
}
```

## 输出建议

```markdown
# 结论
- <当前 decision 的结论；区分来源事实与工程判断>

## 证据
- `<card>#<anchor>`：<事实、revision 与适用边界>

## 冲突或缺口
- <只有存在时输出>

## 建议验证
- <知识证据不能替代的目标平台检查>
```

不要倾倒所有候选。正式交接可附 `cannbot-retrieval-review.v1`，其中 `state_sha256` 绑定 state、`verdict` 为 `approve|reject`；reviewer 只检查覆盖、冲突、边界、receipt 与引用文件一致性，不重新生成工程方案。
