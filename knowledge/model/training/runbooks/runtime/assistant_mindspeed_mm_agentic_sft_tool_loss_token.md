---
{
  "type": "Runbook",
  "title": "MindSpeed-MM agentic LoRA SFT 数据路径：角色不严格交替/tool 结尾轨迹的按角色监督与逐 token 全量校验",
  "description": "框架/任务：MindSpeed-MM，Qwen3.6-27B agentic LoRA SFT（thinking 模式，256K 配置）；数据为 pi 采集的 agent 执行轨迹 JSONL（216→221 条）。；冲突背景：原生转换器要求角色严格交替并以 assistant 结尾。",
  "tags": [
    "task.implementation",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-20T14:17:04Z",
  "platforms": []
}
---

# MindSpeed-MM agentic LoRA SFT 数据路径：角色不严格交替/tool 结尾轨迹的按角色监督与逐 token 全量校验

## 适用场景

- 框架/任务：MindSpeed-MM，Qwen3.6-27B agentic LoRA SFT（thinking 模式，256K 配置）；数据为 pi 采集的 agent 执行轨迹 JSONL（216→221 条）。
- 冲突背景：原生转换器要求角色严格交替并以 assistant 结尾。

## 触发与观测

- 数据画像（source 0 seq 565）：216 条轨迹中 213 条以 `tool` 结束、92 条含连续 assistant 消息。
- 逐条验证：即使补齐 `openai` 配置，当前（原）转换器会丢弃全部 216 条样本；另有 201 条原始构建长度超 64K 上限（source 0 seq 592）。

## 探针与操作

- 新增可选 `agentic_sft` 数据路径（source 0 seq 792 逐字）：保留连续 assistant、用户中途插话和末尾 tool 输出；tool 调用作为训练目标，tool 返回作为上下文且不计算 loss；非思考模式下每条 assistant 消息前的空 `<think>` 块也被屏蔽。
- 数据整理：删除 1,002 条确认失败的 assistant 回复（pi 的 `context_edit` 删除记录未应用问题）、按完整消息边界切分 4 条超长轨迹（最长约 50.9 万 token）→ 221 条训练样本（摘要级，见 dispositions）。
- 全量校验（source 0 seq 1492、2826）：22,125,676（no-think 版）与 42,076,340（thinking 版 221 条）个 token 与官方模板逐 token 一致，loss 标签与 collator padding 检查通过，监督 token 数不变。

## 机制与判别

- 监督语义：真实 thinking、正文和 tool call 参与 loss；tool result、提示内容及 `loss=false` 上下文不作为预测目标；标签只做一次 next-token 移位（source 0 seq 792 及摘要）。
- 判别：`_response` 是中间列名，其中存放工具返回并不意味着训练工具返回（source 0 seq 2873，同轨迹另卡）。
- 与 torchtitan 侧同事适配对照：按整条轨迹渲染、按 assistant 消息位置计 loss，因此不要求角色交替、允许 tool 结尾——agentic 路径对齐该语义（摘要级）。

## 验证信号

- tool_observed：原转换器 216/216 全丢弃的逐条验证（source 0 seq 592）。
- tool_observed：22,125,676 token 与官方模板一致、逐 token loss 标签与 padding 检查通过（source 0 seq 1492）。
- tool_observed：221 条 42,076,340 token 输入与 loss 标签与独立参考一致、监督 token 数不变（source 0 seq 2826）。
- 层级声明：以上是数据链路级验证（CPU/模板级），27B/256K 的 NPU 实训未完成（source 0 seq 1492）。

## 适用与失效边界

- 适用：MindSpeed-MM 对 agent 轨迹（连续 assistant、tool 结尾、用户插话）做 LoRA SFT 的数据接入路径与校验方法。
- 失效/限制：`agentic_sft` 需显式配置；thinking/no-thinking 两模式的监督集合不同（仅含思考的回合在 no-think 下被屏蔽）；多进程 `preprocess` 需固定字段类型（见同窗口 schema 冲突卡）；数据清理决策（删 1,002 失败回复）绑定本批数据来源。

## 附：断言存档

- MindSpeed-MM agentic_sft 数据路径：原转换器因角色不交替/tool 结尾丢弃全部 216 条样本；新路径保留连续 assistant 与末尾 tool、tool 调用作训练目标 tool 返回作上下文不计 loss；221 条 42,076,340 token 逐 token 与官方模板/独立参考一致

```text
保留连续 assistant、用户中途插话和末尾 tool 输出；tool 调用作为训练目标，tool 返回作为上下文且不计算 loss。非思考模式下，每条 assistant 消息前的空 `<think>` 块也会被屏蔽。
```
