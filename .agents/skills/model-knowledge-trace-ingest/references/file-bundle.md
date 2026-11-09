# 批次文件包输出

调用方明确选择 `file-bundle` 时，直接返回一份JSON文件包；不需要列目录、运行shell、写文件或自行校验。调用方负责展开落盘、核对文件并调用离线校验器。此模式只改变产物传输，仍使用相同挖掘方法与证据强度，不调用模型客户端。

```json
{
  "schema_version": "model.trace-file-bundle.v1",
  "batch_manifest_sha256": "调用方提供的实际批清单hash",
  "files": {
    "manifest.json": {"json": {
      "schema_version": "model.trace-mining.v1",
      "sources": [], "coverage": [], "candidates": [], "skipped": []
    }},
    "batch-report.json": {"json": {
      "schema_version": "model.trace-batch-report.v1",
      "batch_manifest_sha256": "同一批清单hash",
      "traces": []
    }},
    "inference/reconstruction.json": {"json": {
      "schema_version": "model.trace-reconstruction.v1", "route": "inference", "traces": []
    }},
    "DRAFT-runtime-example.md": {"text": "# 有证据的独立知识规则\n\n..."}
  }
}
```

示例空数组只表示结构；真实结果必须填写实际来源、覆盖与逐来源去向。没有候选时candidates为空，保留真实原因，不创建空草稿。产物路径是相对路径，JSON产物用json对象、Markdown草稿用text字符串，不双重转义整份JSON。返回完整JSON，不附准备过程或额外解释。

batch-report.traces每项必需字段为trace_id、disposition、candidate_ids、reason，可附routes等补充元数据；disposition取mined/no_knowledge/out_of_scope/deferred。不要以status/notes替代必需字段。零产出/暂缓必须有reason，mined必须列对应candidate_ids。

候选清单沿用 [mining.md](mining.md)：candidate_id、route、draft_path、knowledge_form、sources、evidence_roles、claims和mechanism_artifacts；sources可用顶层来源整数索引。正文的六个章节、四类形态及验证等级保持原合同。修复未验证时采用有证据的诊断或失败形态，不能补写成功信号。

锚点的source是候选内编号。例如候选sources为[2]时，该候选所有锚点的source均为0；sources为[0,2]时，锚点source只能为0或1，分别指向顶层来源0或2。

来源重建以route分组，每份含实际任务、environment、timeline、facts、assumptions、unknowns、limitations、coverage。timeline/facts每项有本来源event_refs。相邻事件不自动构成因果闭环。

读取视图提供每条来源 included_sequences 与 context_only_sequences；有界证据包还提供请求序号、跨页 offset 和 unread_ranges。semantic_review_ranges 只填写实际审阅的完整事件，可是多个不连续区间；未提供的历史系统模板、reasoning 和未读事件不能填成已读。若缺失上下文影响结论，写入 limitations 或将来源 deferred，并区分 unread/missing_evidence/needs_review；不能把准备/传输算成语义理解。

外层保存原始模型响应后，调用离线工具：

```bash
python3 <SKILL_DIR>/scripts/batch_exchange.py unpack <view-or-evidence-dir> <model-response.txt> --output <new-artifacts-dir>
```

unpack 同时接受连续 view 与有界 evidence 目录；核对正文或每页的实际字节/hash 后展开执行 Agent 提供的文件内容，绑定批清单、检查来源/路径/覆盖并执行批级 check。字段、来源编号和知识文本按既定合同验证，不根据一次运行的偏差自动修正。原始响应与文件 hash 保留在 transport-receipt；产物仍是待策展候选，不授予独立审查或发布批准。
