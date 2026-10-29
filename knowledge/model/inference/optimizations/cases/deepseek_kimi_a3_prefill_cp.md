---
type: Optimization
title: DeepSeek/Kimi A3 Prefill CP：整域约束与阶段门控
description: 记录两个固定 cann_executor 实现的 cp_size 等于 world_size 校验、ZigZag 与 KV 汇聚；DSA 细节和 Kimi 部署规模分别说明，不推广到 SGLang。
tags:
- task.optimization
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/fa6892b54681724ac433118b2088ac9b614779f6/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/da13d661535741e1b2f3d6c1443a422af54150ba/docs/models/kimi-k2-thinking/kimi_k2_thinking_inference_guide.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/fa6892b54681724ac433118b2088ac9b614779f6/models/deepseek-v3.2-exp/infer.py
  role: constraint
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/da13d661535741e1b2f3d6c1443a422af54150ba/models/kimi-k2-thinking/infer.py
  role: constraint
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/fa6892b54681724ac433118b2088ac9b614779f6/models/deepseek-v3.2-exp/models/modeling_deepseek.py
  role: implementation
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/da13d661535741e1b2f3d6c1443a422af54150ba/models/kimi-k2-thinking/models/modeling_deepseek.py
  role: implementation
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/fa6892b54681724ac433118b2088ac9b614779f6/models/deepseek-v3.2-exp/config/deepseek_v3.2_exp_rank_64_64ep_prefill.yaml
  role: example
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/da13d661535741e1b2f3d6c1443a422af54150ba/models/kimi-k2-thinking/config/kimi_k2_thinking_rank_64_64ep_prefill.yaml
  role: example
created_at: '2026-10-20T12:16:14Z'
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
        - mla
      framework:
      - cann_executor
---

# DeepSeek/Kimi A3 Prefill CP：整域约束与阶段门控

## 条件与规则入口

本案例补充[长序列 CP 决策](../rules/long_seq_prefill_context_parallel.md)，限定 Atlas A3、Prefill，以及 DeepSeek-V3.2-Exp `fa6892b54681724ac433118b2088ac9b614779f6`、Kimi-K2-Thinking `da13d661535741e1b2f3d6c1443a422af54150ba` 两个 cann_executor 固定实现；不能直接用作 SGLang 配置。

## 两个实现共同的边界

两者的 `infer.py:check_parallel_settings` 都在 `cp_size > 1` 时要求 `cp_size == world_size`。对应 Prefill 样例均为 `world_size=64, cp_size=64`；这是固定入口的硬校验，不是 CP 技术的通用限制。

建模按 `is_prefill` 选择 CP 路径；例如有效 CP 大小在 Decode 按 1 处理。序列按 `cp_size * 2` 分块，每个 rank 负责头尾对称块，并在需要处恢复因果 token 顺序。局部 Q 配合 CP 域汇聚的 KV 计算；LM Head 前也有汇聚与重排，不能只切 input 而省略配套路径。

MoE 的 EP 与整域 CP 在这组配置中覆盖相同 rank 集合，但 `init_parallel_comm_group` 分别初始化 `moe_ep_group` 和 `cp_group`。文档的“复用通信域”不能改写成“源码不再建组”或两个对象必然相同。

## 模型各自的差异

DeepSeek 使用 DSA：其官方文档说明 Indexer 的 head 归约与额外通信，不能把该论据用于所有稠密注意力。Kimi 文档说明单机与多机长序列部署示例；4K、256K 和节点数是该版本实践的描述，不是两模型共同的长度或规模阈值，也不是本次独立测得的上限。

输出投影、Embedding 与 LM Head 的 TP 仍有自己的布局和通信约束；它们不改变 CP 的阶段边界。跨 Prefill/Decode 迁移规模时，另读[集群配置核对](../rules/prefill_decode_cluster_scale_mismatch.md)。

## 验证与回退边界

来源没有只改变 CP 的独立收益数据。本次静态核对入口、分组与阶段门控，没有执行模型。复现需检查 token/position 与 KV 的顺序、因果掩码、通信组、输出与 TTFT；恢复配置也需重核缓存和组布局，不将历史样例视为可直接运行的当前配方。
