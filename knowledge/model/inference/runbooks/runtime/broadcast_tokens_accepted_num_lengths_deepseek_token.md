---
{
  "type": "Runbook",
  "title": "DeepSeek V4 投机推理 TP 下 accepted_num 未同步导致各 rank KV 状态分歧（PR804 审查发现）",
  "description": "模型/框架：DeepSeek V4 在 cann-recipes-infer 的公共投机推理采样路径（execution_engine.py，PR #804 head bf24d16 新增 TP 分支）。；环境：审查环境 CPU 复现（NPU 算子 mock）；目标环境为多 rank TP 推理。",
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

# DeepSeek V4 投机推理 TP 下 accepted_num 未同步导致各 rank KV 状态分歧（PR804 审查发现）

## 适用场景

- 模型/框架：DeepSeek V4 在 cann-recipes-infer 的公共投机推理采样路径（execution_engine.py，PR #804 head bf24d16 新增 TP 分支）。
- 环境：审查环境 CPU 复现（NPU 算子 mock）；目标环境为多 rank TP 推理。
- 目标：审查投机推理验证结果在 TP rank 间的同步完整性。

## 触发与观测

- 公共采样逻辑只广播 token，不同步接受长度："`accepted_num` 在广播前由各 rank 独立计算，随后仍用于选择 draft 输入和 KV 位置。CPU 复现中，广播后 token 相同，但接受长度为 `0 / 2`，下一轮 KV 长度为 `12 / 14`。需要在消费验证结果前同步接受状态。"（source 0 seq 187）
- 探针逐字输出："SPEC: broadcast tokens=[[1, 0, 0]], accepted_num=[0, 2], next KV lengths=[12, 14]"（source 0 seq 164/165）。

## 探针与操作

- CPU 复现探针（source 0 seq 161 脚本，AST 提取真实函数、mock broadcast）：广播仅 token，两 rank 的 accepted_num 保持 [0, 2]，下一轮 KV 长度分叉为 [12, 14]。
- 定位：`executor/core/engine/execution_engine.py:974-978`；修复方向是在消费验证结果前同步接受状态（broadcast accepted_num）。

## 机制与判别

- 根因：投机验证后各 rank 的接受长度存在数值不确定性来源（如采样边界），只广播 token 不广播 accepted_num 时，rank 间 KV 长度与 draft 输入选择可能分叉，后续轮次读到不一致的 KV 位置。
- 判别：token 一致但 KV 长度不一致（12 vs 14）是本故障的可区分签名；若 accepted_num 在所有 rank 严格同源则不触发。
- 未验证：NPU 多 rank 整网运行中的实际触发频率（CPU 逻辑复现）。

## 验证信号

- tool_observed（CPU mock，source 0 seq 164/165）：SPEC 输出如上；同脚本 ATTENTION/O-proj TP 分片代数检查通过（探针自检）。
- 单次逻辑复现；非设备验证。

## 适用与失效边界

- 适用于：cann-recipes-infer 投机推理（MTP/DSpark 等）引入 TP 后的采样同步审查。
- 失效边界：单 rank（无 TP）或 accepted_num 严格确定性的实现不触发；结论基于 PR #804 bf24d16，后续提交可能已修复。
- 停止条件：核查当前代码在消费前已同步 accepted_num 即失效。

## 附：断言存档

- DeepSeek V4 投机推理 TP 公共采样只广播 token 不同步 accepted_num：CPU 复现实测广播后 token 相同（[[1,0,0]]）但接受长度分叉 [0,2]、下一轮 KV 长度 [12,14]；accepted_num 随后仍用于选择 draft 输入和 KV 位置，须在消费验证结果前同步。
