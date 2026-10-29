---
type: Optimization
title: 长序列 Prefill 的 CP 决策：按注意力结构与实现选择切分
description: 在已有 A3 MoE 实践中，按长序列 Prefill 的激活显存、TTFT 与通信开销评估 CP；DeepSeek/Kimi 整域 CP 与 Qwen3-Next/SGLang CP+TP 的实现条件分别进入案例。
tags:
- task.optimization
- topic.attention
- topic.mixture_of_experts
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/fa6892b54681724ac433118b2088ac9b614779f6/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/da13d661535741e1b2f3d6c1443a422af54150ba/docs/models/kimi-k2-thinking/kimi_k2_thinking_inference_guide.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/874b41df5de8107dd241c2cd2ac0712ad3a758a0/docs/models/qwen3-next/qwen3_next_optimization.md
  role: supporting
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-20T12:49:18Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - prefill
      objective:
      - latency
      - ttft
      - memory
      context_length:
      - long_context
      - ultra_long_context
      model_features:
        all_of:
        - moe
---

# 长序列 Prefill 的 CP 决策：按注意力结构与实现选择切分

## 适用场景与问题信号

本规则面向已有 Atlas A3 证据的 MoE 长序列 Prefill：单 rank 的注意力计算或激活显存随序列增长，出现 TTFT 压力或 OOM 风险时，评估沿序列维做[上下文并行](../../concepts/parallelism/context_parallel.md)。不将具体模型的长度样例写成通用阈值，也不声明每个长请求都优于 TP 或 DP。

## 决策与机制

先确认瓶颈属于注意力计算、激活、权重还是路由负载，再比较合法的并行方式。CP 把查询 token 分给多个 rank，配合 KV 汇聚和布局恢复，目标是分摊长序列计算与激活；代价包括通信、重排以及部分路径对完整 KV 的持有。收益不能只由分片比例推导。

DSA 的 Indexer、稠密 MLA 与混合注意力有不同代价。DeepSeek 的文档以 Indexer 的 head 归约说明纯 TP 的额外通信；Qwen3-Next 则将 Gated Attention 采用 CP+TP、GDN 保留 TP。不能把某一模型的“CP 优先”推广成所有注意力都禁用 TP。

因果负载不均时可评估 ZigZag；是否开启、如何恢复 token 顺序和写入 KV，必须依照对应实现。[ZigZag 分段计算](causal_cp_prefill_zigzag_actual_seqlens.md)与[MLA-prolog KV 写入约束](mla_prolog_zigzag_cp_kv_write.md)作为相关决策单独维护。

## 实施入口与边界

- [DeepSeek/Kimi A3 整域 CP 案例](../cases/deepseek_kimi_a3_prefill_cp.md)：固定入口要求启用 CP 时 `cp_size == world_size`，建模按 Prefill 门控，记录序列切分、KV 汇聚和通信组的边界。
- [Qwen3-Next A3/SGLang CP+TP 案例](../cases/qwen3_next_a3_prefill_cp_tp.md)：记录 Gated Attention/GDN 分层处理、ZigZag、PD 分离和通信域限制。

上面两类实现共享优化选择，不共享一套参数。整域 CP、MoE 复用通信域、节点数或 PD 限制只在各自证据范围内成立。新案例不因链接本规则而获得另一实现的条件。

## 收益、风险与回退

来源说明降低激活压力和改善 TTFT 的目标，但没有隔离 CP 开关的独立受控对比；本次未运行模型。通信开销、重排错误、KV 写入或因果掩码错误都可能抵消收益或影响正确性。

调整前保存合法配置与输出基线；按对应版本恢复原并行方式，并核对缓存布局和通信组，不能只删一个 CP 参数就认为已完成迁移。回退后仍须验证输出及显存、TTFT。

## 验证方法

固定模型与源码版本、平台、量化、输入分布、batch 和部署规模，比较合法的基线与 CP 配置。分别记录注意力和通信时间、激活与 KV 峰值、TTFT、重复次数与波动，以及输出验收。Decode 是否使用 CP 必须读阶段门控；KVP 的历史机制与撤回状态见 [KVP Concept](../../concepts/parallelism/kvp.md)，不提供当前启用建议。

## Evidence

固定 DeepSeek、Kimi 与 Qwen3-Next 官方优化文档支撑本规则的 A3 范围与选择依据。参数、入口校验和源码差异在对应案例保留固定文件；没有增加 `verified` 或量化收益承诺。
