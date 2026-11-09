# 模型轨迹知识的独立审查

审查者以独立、只读上下文阅读冻结 subject、[证据合同](runbooks-contract.md)、账本、重建、最终卡、相关规范化原文和合并前旧卡，不执行轨迹命令。

逐项检查：

- 归一化是否准确区分角色、调用与返回，unknown、媒体、截断和缺失子会话是否影响结论；自动解析不授予语义覆盖。
- 结论是否属于模型训练/推理优化、框架适配或相关环境调试调优；是否包含与本领域无关的事实。
- 候选和来源去向是否完整，跨轨迹合并是否保留独立实验边界，同源副本是否误算复现。
- 每条结论是否有完整机制、客观信号与实际锚点；正文中的额外技术判断也须复核。
- 源码版本、修改和运行结果是否对应，是否把用户叙述或 Agent 推测当设备事实，是否将多变量变化归因到单一原因。
- 性能是否有可比模型、硬件、精度、负载、并行与统计口径，单次结果是否被不当外推。
- 私有账号、连接信息、原始对话和取证路径是否泄漏到公开卡；适用与失效边界是否充分。

标题和摘要与正文同等核验：不能保留账本已删掉的收益、因果或 API 断言。逐字出现不证明代码单元完整，须检查输入约束、完整函数/配置、参考预期、实际验证及版本是否配套；单行调用不能替代整个机制。未记录、源端截断、显示精度舍入为零均不能当作反证或真实零值。源码阅读、静态检查、CPU 参考、设备功能、端到端和性能验证分别审查，不能由路径名或 Agent 叙述升级等级。

审查者从原文建立判断，不沿用挖掘者预填的目标结论。不同基线、忽略输入约束、缺参考变换、无证据的排序/精度承诺和未闭合反例均属语义问题；必须修订、删去对应断言或暂缓，并在新冻结内容上重新审查。

通过实际运行时返回 `model.trace-review.v1` JSON：

```json
{
  "schema_version": "model.trace-review.v1",
  "subject": {"说明": "完整复制 review_cards.py subject 输出对象"},
  "verdict": "PASS 或 NEEDS_REVISION",
  "summary": "实际审查结论",
  "findings": [],
  "coverage": [{
    "path": "runtime/example_slug.md",
    "claim_ids": ["实际全部采用claim id"],
    "checked": ["scope", "title", "description", "body", "source_authority", "validation_scope", "comparisons", "contradictions"],
    "complete_artifact_indexes": [0],
    "unmapped_assertions": []
  }],
  "reviewer": "实际运行时审查者身份",
  "attestation": "agent-runtime-message",
  "reviewed_at": "实际 UTC 时间"
}
```

每条 finding 包含 severity（blocker/major/minor）、category、card、issue、location、suggestion。category 为 evidence/scope/api_contract/causality/comparison/validation/privacy 时，无论 severity 如何都须 NEEDS_REVISION；新合同只容许不改变知识含义的 format/clarity minor 留在 PASS，所有 blocker/major 均阻断。

新 curation_contract 的 coverage 每卡恰好一项，claim_ids 与 subject 中列表一致，complete_artifact_indexes 覆盖所有完整机制单元，checked 覆盖 subject.required_checks，unmapped_assertions 必须为空才能 PASS。不能默认填齐：尚未查明的正文断言应列出并退回修订。旧账本无强制 coverage，但不得声称完成新合同覆盖。

subject 使用规范化后的实质 ledger hash（将两类批准标记置回待审），与磁盘 ledger 的原始文件 hash 可能不同；完整复制工具实际输出，不能自行计算替代。不能通过运行时身份核验时保留待审，receipt 的字段、覆盖声明和 hash 均不认证审查者身份或阅读事实。

逐卡检查[脱敏与自包含](privacy.md)：私有账号、工作目录、模型/数据集位置、内网连接、工具元数据及代码块全部覆盖；不能以变量或删词掩盖缺失的实验条件。核对工具退出码与截断标记，拒绝从 completed/PASS 推导成功。范围关系须有实际模型/框架观测，不能只有背景关键词。

检查重建每个非未知环境字段与同来源 facts/事件是否一致，特别防止并行、精度、offload 等条件被跨来源复制。区分“before 配置原值”和“before 运行已经失败”，没有运行观测时不能写成观测。正文中超出 claim 的通过标准或判读分支列入 unmapped_assertions；来源归属错误、重建事实冲突和验证规则越界属于 evidence/validation 问题，不能以 clarity minor 放行，也不能以尚无下游采用降级。
