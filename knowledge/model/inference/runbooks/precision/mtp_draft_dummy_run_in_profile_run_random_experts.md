---
type: Runbook
title: MoE + 投机解码：draft dummy_run 误带 profile-run 语义触发强制随机专家路由，静默拉低 MTP accept rate
description: 记录 vLLM-Ascend PR5093 对 draft dummy_run 的 profile 标志修正；检查强制均衡、路由及实际状态消费链，再验收接受率，不把低接受率直接归因于 dummy_run。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.speculative_decoding
- topic.parallelism
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/5093
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/eb4c08f05dac1ae5d12bd9aa7e4aa76a4ab72032/vllm_ascend/spec_decode/mtp_proposer.py
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-10-22T10:43:19Z'
platforms:
- agnostic
---

# MoE + 投机解码：draft dummy_run 误带 profile-run 语义触发强制随机专家路由，静默拉低 MTP accept rate

## 信号（现象）

在昇腾 NPU 上给 **MoE 模型接 [MTP / EAGLE 投机解码](../../concepts/techniques/mtp_speculative_decoding.md)**，decode 阶段观测到 **MTP accept rate（草稿 token 被主模型接受的比例）明显偏低**，但不报错、不告警、精度没崩，只是投机收益远低于预期。这类「投机开了、accept rate 却上不去」的场景，若 draft 模型走的是 MoE 前向，优先怀疑 draft 模型的预热 / 占位前向（`dummy_run`）是否把 **profile-run 语义**误带进了会影响路由的路径——它会让 MoE 强制随机选专家，可能改变该前向的输出；是否传播到正式草稿或状态须进一步取证。

本页范围的判定条件：
- draft（草稿）模型本身是 MoE（走 fused-MoE / [EP](../../concepts/parallelism/expert_parallel.md) 前向），而非 dense 小模型；
- accept rate 低是**稳态、持续**的（不是首步冷启动个例）；
- draft 的路由应符合其训练和部署约定；随机覆盖可能改变输出，但不要求 draft 与主模型具有相同专家或路由。是否造成持续接受率下降需验证实际消费链。

## 触发条件

昇腾 forward context 有一个 `in_profile_run` 标志，本意标记「这是一次显存 / 负载 profiling 的占位前向」。MoE 前向读它决定是否**强制负载均衡**：

- `enable_force_load_balance = forward_context.in_profile_run`；
- 当 `enable_force_load_balance` 为真时，MoE 用 `torch.rand` 生成随机矩阵、`argsort` 取前 topk **覆写 `topk_ids`**（量化路径 w8a8-dynamic / w4a8-dynamic 同样如此），即**强制随机选专家**。

该随机化在真正的 profile run 中用于合成负载，不代表真实路由。PR5093 报告移除 draft dummy_run 的 in_profile_run 标志后接受率问题得到修复；已核实的链仅到 profile 标志覆盖专家选择。固定 dummy_run 并未消费该次 model 返回值，从占位前向到正式草稿或持久状态的传播仍需取证，不能宣称已确认草稿分布污染或以主/副路由不同解释接受率下降。

## 根因

`in_profile_run` 触发的强制随机专家（force-load-balance）本身没错，错在**语义误用**：spec-decode 的 draft `dummy_run` 不该复用 profile-run 语义。

已核对的机制链是 profile 标志触发强制均衡、覆盖 router 的专家选择。PR 将去掉 draft dummy_run 的该标志与接受率修复关联；从 dummy 输出到正式草稿/状态的传播链仍须按目标版本取证。

是否影响真实输出或后续状态，必须沿实际调用链确认；不能仅凭 dummy_run 使用 profile 标志，就认定产生了线上草稿污染。PR5093 将该标志误用与接受率修复关联，但未给出完整状态污染链和量化前后结果。

## 修法

让 draft 模型的 `dummy_run` **不进入 profile-run 语义**，即设置 forward context 时**不传 `in_profile_run=True`**，回落默认 `False`：

- eagle / mtp 两个 proposer 的 `dummy_run` 中，`set_ascend_forward_context(...)` 去掉 `in_profile_run=True`；
- forward context 里对 MTP 模型的 `moe_comm_type` 覆写（如 `FUSED_ALLTOALL → ALLTOALL`）不再 gate on `in_profile_run`，改为只 gate on `is_mtp_model`——即该覆写本就该在 MTP 模型上无条件生效，不该借 `in_profile_run` 触发。

来源修正后的路径：draft `dummy_run` 里 `in_profile_run == False` → `enable_force_load_balance == False` → MoE 用**真实 router 的 `topk_ids`**、不再随机覆写 → draft 走真实专家路由 → 需在目标请求上重新测量接受率；“fix mtp accept rate”为 PR 的定性说明。

**边界**：这里修的是「draft dummy_run 误用 profile 语义」，**不是**说 profile run 的 force-load-balance 有害——在真正的显存 / 负载 profiling 场景，随机专家均衡负载是有意行为，应保留。判据是：这次前向的**输出是否会影响真实结果 / 命中率**。是（如 draft 产草稿）→ 不能带 profile 语义；纯占位测显存 → 可以。

## 参考实现及其约束

- 参考实现：vllm-ascend（vLLM 昇腾 NPU 后端），vLLM v0.12.0。涉及 `spec_decode/eagle_proposer.py`、`spec_decode/mtp_proposer.py`、`ascend_forward_context.py`（删改点）与 `ops/fused_moe/fused_moe.py`（机制端），具体见 Evidence。
- 约束：`enable_force_load_balance = forward_context.in_profile_run` 这一等式、以及「force-load-balance 用随机 topk_ids 覆写真实路由」的实现，是 **vllm-ascend 自有的 Ascend forward-context + fused-MoE 机制**；其他框架的 profile / dummy-run 未必同样把随机专家均衡挂在同一个标志上。可迁移的是**思想**（占位 / profile 前向若复用到会影响真实输出的路径、且该前向路径带有「随机化 / 均衡」这类 profile-only 副作用，就会污染结果），落地时须核对本框架里 profile 标志各自触发了哪些副作用。

## 相关经验
- [profile_run 峰值显存低估致运行期 OOM：profiling 未实际走一遍所有影](../performance/profile_run_peak_memory_underestimate_untraversed_path.md)

- MoE 优化在 decode 静默失效的其他根因（硬编码 False / yaml 键名不匹配 / 漏切间接层 / 误挂 is_prefill）：[MoE 优化/并行在 decode 静默不生效的四类根因](../performance/moe_optimization_silently_disabled_decode.md)。
- 投机解码上线前置条件：[MTP 投机解码 graph-mode 前置](../runtime/mtp_speculative_decode_graph_mode_prereqs.md)、[MTP 投机解码模型接入](../../guides/integration/mtp_speculative_decode_model_onboarding.md)。

## Evidence

- draft dummy_run 去 `in_profile_run=True`（`eagle_proposer.py`、`mtp_proposer.py`）+ `is_mtp_model` moe_comm_type 覆写去 `in_profile_run` gate @merge sha `eb4c08f05dac1ae5d12bd9aa7e4aa76a4ab72032`（vLLM v0.12.0）。
- 机制端因果链 `enable_force_load_balance = forward_context.in_profile_run`（`fused_moe.py`）+ 随机矩阵 `argsort` 覆写 `topk_ids`（`fused_moe.py`，量化路径 `w8a8_dynamic` / `w4a8_dynamic` 同）@同 sha。
- 根因表述（review 讨论）：「in moe, if in_profile_run, the experts will be forced to choose random experts」；accept-rate 无 before→after 数字，仅定性「fix mtp accept rate」。
- 溯源下探：[vllm-ascend-pr-5093-bugfix-fix-mtp-accept-rate](https://github.com/vllm-project/vllm-ascend/pull/5093)。

## 探针、验证与停止条件

在不改变真实 router 的前提下记录 proposer 路径、`in_profile_run`、`is_mtp_model` 和强制均衡开关；分别检查真实 profiling、draft dummy 与正式推理。若怀疑状态污染，还须证明该前向结果或写入状态被后续请求消费。修正后用同一权重、输入和采样比较接受数及输出；真实显存 profiling 的均衡语义应继续保留。证据链不符时转查隐状态与缓存记账，不把低接受率归因于此。
