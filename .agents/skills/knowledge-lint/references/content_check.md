# Content Check

页面内容审阅是明确指定页面时才启用的只读语义检查，不代替 `knowledge_lint.py` 的确定性治理。

Reviewer 只读取仓库快照，不发起网络请求；外部来源无法从仓内证据确认时保持不报告。

## 检查项

`content_check.toml` 是启用项、严重度、公开模型别名、凭据环境、并发、超时、重试和页面上限的事实源。模型 ID 由 `MODEL` 提供，端点与令牌由 `BASE_URL`、`AUTH_TOKEN` 提供；这些值只在实际启动 reviewer 时读取，不写入计划、结果或 Summary。`content_check_prompt.md` 定义 reviewer 的证据边界和页面 JSON 格式。

## 页面协议

页面结果必须是一个 JSON object：key 与全部启用检查 ID 完全一致。每个 value 是违反项数组；每项只有非空 `msg` 和正整数或 `null` 的 `line`。行号不得超过页面实际行数。

## 汇总协议

`scripts/content_protocol.py` 严格校验选页计划、页面结果、核心汇总和退出码一致性。页面未完成进入 `errors`；仓库、选页或协议级故障进入 `runtime_error`，不计入未完成页数。

Finding 展示前按 P0、P1、P2、页面路径、行号、检查 ID 和消息排序。页面级结果不允许缺项、多项、重复页面、非有限 usage 或与选页计划不一致的覆盖范围。
