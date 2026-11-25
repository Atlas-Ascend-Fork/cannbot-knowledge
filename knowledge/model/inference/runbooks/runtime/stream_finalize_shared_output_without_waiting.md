---
{
  "type": "Runbook",
  "title": "DeepSeek V4 多流 MoE TP 共享专家副流输出缺 wait_event 竞争（PR804 审查发现）",
  "description": "模型/框架：DeepSeek V4 在 cann-recipes-infer 的多流 MoE（enable_multi_streams，共享专家副流计算）+ MoE TP 路径（PR #804 head bf24d16）。；环境：审查环境 CPU 复现（mock stream/event 语义）；目标环境 NPU 多流。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-20T14:17:06Z",
  "platforms": []
}
---

# DeepSeek V4 多流 MoE TP 共享专家副流输出缺 wait_event 竞争（PR804 审查发现）

## 适用场景

- 模型/框架：DeepSeek V4 在 cann-recipes-infer 的多流 MoE（enable_multi_streams，共享专家副流计算）+ MoE TP 路径（PR #804 head bf24d16）。
- 环境：审查环境 CPU 复现（mock stream/event 语义）；目标环境 NPU 多流。
- 目标：审查多流共享专家输出在主流消费前的同步。

## 触发与观测

- "多流 MoE TP 缺少共享专家完成事件的等待 —— 开启多流时，共享专家在副流计算，但主流的 `wait_event` 被注释，直接通过 `skip1` 读取结果，存在读取未完成数据的竞争。应恢复 finalize 前的等待。"（source 0 seq 187）
- 探针逐字输出（source 0 seq 164/165）：
  "STREAM: finalize reads side-stream shared output without waiting for event 1"
  "STREAM: positive control with restored wait passes"

## 探针与操作

- CPU 探针（source 0 seq 161）：mock `wait_event`（仅在 enabled 且 idx==1 时置 ready）与 `npu_moe_finalize_routing`（断言 ready），AST 提取真实 `DeepseekV3MoE.moe_infer_tp` 运行——PR 分支断言失败（未等待即消费）；恢复 wait 的正对照通过。
- 定位：`models/deepseek_v4/models/modeling_deepseek.py:439`。

## 机制与判别

- 根因：多流路径删除/注释主流对共享专家副流 event 的等待，finalize 读 `skip1` 时副流可能未写完 → 数据竞争，症状可为偶发错误值或设备异步错误。
- 判别：恢复 wait_event 的正对照通过，说明竞争由缺等待引起而非输出本身错误。
- 未验证：NPU 实机多流运行的偶发率（CPU 逻辑复现）。

## 验证信号

- tool_observed（CPU mock，source 0 seq 164/165）：两条 STREAM 输出如上；单次复现＋正对照。
- 非设备验证。

## 适用与失效边界

- 适用于：cann-recipes-infer 多流 MoE（共享专家副流）改造审查。
- 失效边界：单流或共享专家在主流计算的路径不触发；结论基于 PR #804 bf24d16，后续提交可能已恢复等待。
- 停止条件：核查当前代码 finalize 前 wait_event 存在即失效。

## 附：断言存档

- DeepSeek V4 多流 MoE TP 中共享专家副流输出在主流消费前缺 wait_event（被注释，经 skip1 直接读取）：CPU 探针实测 finalize 未等待即读副流输出，恢复等待的正对照通过；存在读取未完成数据的竞争。

```text
STREAM: finalize reads side-stream shared output without waiting for event 1
STREAM: positive control with restored wait passes
```
