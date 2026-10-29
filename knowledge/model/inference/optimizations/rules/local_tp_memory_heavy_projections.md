---
type: Optimization
title: 局部 TP：Attention DP 下 o_proj / dense MLP 的 DP→TP→DP 边界通信
description: 在 A3 MoE Decode、Attention DP + MoE EP 下，对 o_proj、dense MLP、LM Head、Embedding 单独局部 TP 以减少单卡显存和权重搬运；核对 DP→TP→DP 布局转换与 AllGather / ReduceScatter 通信，切分实现见案例。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/da13d661535741e1b2f3d6c1443a422af54150ba/docs/models/kimi-k2-thinking/kimi_k2_thinking_inference_guide.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/da13d661535741e1b2f3d6c1443a422af54150ba/models/kimi-k2-thinking/models/modeling_deepseek.py
  role: implementation
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/docs/models/longcat-flash/longcat_flash_optimization.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/d6ba03b342efe7eecb814cb4657242e28894093a/models/longcat-flash/models/model_setting.py
  role: constraint
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/54
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/6cb49951ea22220608ad08d278b4e0c779e870eb/module/linear.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-22T06:30:56Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
      objective:
      - memory
      - latency
      - tpot
      model_features:
        all_of:
        - moe
      parallelism:
        all_of:
        - dp
        - ep
---

# 局部 TP：Attention DP 下 o_proj / dense MLP 的 DP→TP→DP 边界通信

## 适用条件与决策

本卡是局部 TP 的统一规则入口，主结论限定已有 Atlas A3 证据的 MoE Decode：Attention 使用 [DP](../../concepts/parallelism/data_parallel.md)，MoE 使用 [EP](../../concepts/parallelism/expert_parallel.md)，部分投影权重的复制、读取或显存占用成为瓶颈。Scope 只描述这一主结论；后面的 Prefill 排查与 Embedding 初始化修复是带独立边界的参考，不据此扩大阶段或平台。

先从 profiling 和显存观测确认压力所在，再选择 o_proj、LM Head、Embedding 或 dense 层做[局部 TP](../../concepts/parallelism/tensor_parallel.md)。目标是减少这些层在单 rank 的权重占用或搬运；同时要计入层前后 DP/TP 布局转换的通信代价。不要仅因模型用了 MoE 就假设每一层都适合加 TP。

## 选择、前提与验证

| 选择 | 必须核对的前提 | 验证重点 |
|---|---|---|
| o_proj 局部 TP | 当前模型的权重输入维、分片整除和 Attention 输出布局 | 投影时延、权重访存与转换通信 |
| dense MLP 局部 TP | gate/up、down 的分片方向及层前后布局恢复 | 分片后的显存、AllGather/ReduceScatter 与输出 |
| LM Head / Embedding TP | 词表分片、rank 偏移、输出合并及模型配置项名称 | 权重显存、加载峰值和 token/logits 正确性 |

Kimi 固定实践将局部 TP 通信限制在节点内高速互联域，以降低跨节点通信代价；迁移时应核对真实拓扑，不能把“节点内”直接替换为任意固定 TP 数。Kimi 使用 `oproj_tp_size`，LongCat 使用 `o_proj_tp_size`，两者不能照抄字段名。

`attn_tp_size == 1` 是本卡所讨论 Attention-DP 路径的条件，**不意味着所有模型都禁止 Attention TP 与 o_proj TP 同时大于 1**。例如 LongCat 在 `d6ba03b342efe7eecb814cb4657242e28894093a` 中要求 `attn_tp_size > 1` 时两者相等。跨模型迁移必须读取目标版本的校验与前向分支。

固定 LongCat 的 o_proj K 轴 TP、dense MLP 切分与边界通信只维护在 [LongCat A3 案例](../cases/longcat_dp_tp_projections.md)，本规则不复制模型实现步骤。

## 补充参考的适用边界

[Issue 54](https://gitcode.com/cann/cann-recipes-infer/issues/54) 的 DeepSeek-V3.2-Exp W8A8C8 单机记录包含 Prefill `HcclAllGather` 处的 `EL0004`，回复建议减 batch、增大 oproj/dense TP。后续记录也出现了 `batch_size=1` 不满足 DP 整除的错误，最终讨论还涉及其他问题；不能把这组建议写成“改为 1 即可修复”的已验证配方。该记录是显存排查线索，不是主 Scope 的 Prefill 收益证明。

[PR472 的固定实现](https://gitcode.com/cann/cann-recipes-infer/blob/6cb49951ea22220608ad08d278b4e0c779e870eb/module/linear.py) 将 `VocabParallelEmbedding` 的父类初始化大小设为 `input_size_per_partition`，直接分配词表分片，避免先按完整词表分配再覆盖。它解决初始化时的分配问题，不能自动等同于 Decode 时延收益，也不为本规则增加平台适用性。

## 收益、失败边界与复现

Kimi 与 LongCat 文档提供机制和定性优化目标，没有可归因于单一局部 TP 改动的独立 before/after。静态分片证据不能证明端到端净收益。

验证时固定模型版本、输入与输出长度、batch、量化及其他开关；比较显存峰值、投影与通信时间、Decode 时延或 TPOT，并检查输出。若新增通信抵消计算/访存收益、分片不整除或布局不一致，应恢复原并行配置并重新核对路径。本次没有执行模型或增加 `verified`。

## Evidence

- [Kimi 推理实践](https://gitcode.com/cann/cann-recipes-infer/blob/da13d661535741e1b2f3d6c1443a422af54150ba/docs/models/kimi-k2-thinking/kimi_k2_thinking_inference_guide.md)：核对 A3、Decode Attention DP + MoE EP、投影与词表权重的局部 TP 目标及节点内通信范围。
- [Kimi 建模](https://gitcode.com/cann/cann-recipes-infer/blob/da13d661535741e1b2f3d6c1443a422af54150ba/models/kimi-k2-thinking/models/modeling_deepseek.py)：核对 oproj AllToAll/ReduceScatter、Embedding 词表偏移及合并、LM Head 分片；这些层并不共享一套固定通信序列。
- [LongCat 优化文档](https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/docs/models/longcat-flash/longcat_flash_optimization.md)及[并行校验](https://gitcode.com/cann/cann-recipes-infer/blob/d6ba03b342efe7eecb814cb4657242e28894093a/models/longcat-flash/models/model_setting.py)：核对案例证据与不同路径的约束差异。
- Issue 54 与 PR472 只支撑上面的独立参考段落，不扩展主结论的 Scope。
