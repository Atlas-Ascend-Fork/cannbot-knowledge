---
type: Concept
title: Packed Sequence：请求边界、长度与 KV 映射
description: 区分 packed token、普通长度、累计长度和 slot_mapping，说明 Prefill/Decode 输出及并行通信必须保留请求对应关系。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/design/packed_sequence_design.md
  role: primary
created_at: '2026-10-29T04:09:04Z'
updated_at: '2026-10-29T12:00:02Z'
platforms:
- agnostic
---

# Packed Sequence：请求边界、长度与 KV 映射

## 机制

Packed Sequence 把每个请求的有效 token 按请求顺序拼为一维输入，边界由元数据描述。长度 [5,2,3] 的累计结束偏移是 [5,7,10]，采用右开区间；它与每请求的普通长度不是同一个量。

input_ids、position_ids 和写入 KV Cache 的 slot_mapping 必须逐 token 对齐。position_ids 表示请求内部的位置，不是 packed 批次的全局偏移。block_table 按请求定位物理缓存块。

## 阶段与输出

Prefill 的当前 Q 长度通常为本次请求输入长度；Decode 的当前 Q 长度由每请求本步提交的 token 数决定，历史 KV 长度独立增长。模型须按实际算子接口选择普通长度、累计长度及图模式使用的 host list，不能将 packed 全批视作单一序列。

该版本 Executor 约定 Prefill 返回每请求最后一个 token 的 logits，形状 [B,1,V]；Decode 返回 [B,q_len,V]。静态 batch 的补齐位置在采样后按真实请求数截去，不更新真实请求状态。多模态视觉 embedding 另由顶层参数传入，不放进 ForwardMetaData。

## 并行边界与验证

相同请求数不保证相同 token 数。Attention DP 下的变长输入可能导致 TP/EP 集合通信 shape 或 MoE chunk 次数不同；需核对通信次数、顺序、补齐及 CP metadata，不能仅比较 batch 数。

用不等长多请求分别执行与拼接执行对比，检查跨请求隔离、末 token 选择、slot 写入、Decode 历史长度及补齐截断。收益来自减少 padding，额外成本是边界元数据与布局处理；文档未给通用加速比。

## Evidence

固定 Packed Sequence 设计文档及其中 Qwen3-MoE 的接口示例。本卡描述布局契约，具体模型与算子重载需继续读对应实现。
