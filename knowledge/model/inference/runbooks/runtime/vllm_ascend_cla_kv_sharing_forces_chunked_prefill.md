---
type: Runbook
title: 跨层 KV-sharing（CLA）模型在昇腾上误选 PrefillNoCache：共享层要读别层写入的 KV cache，须强制 ChunkedPrefill
description: 昇腾 backend 上跨层 KV-sharing（cross-layer attention, CLA）模型（如 gemma-3n，配置带 shared_kv_cache_layers）会误选 PrefillNoCache attention state，导致共享层读不到目标层写入的 KV cache、输出与 eager/GPU 对不上。信号：CLA 模型共享层正确性异常（读到空/错 cache），发生在 vLLM-Ascend 的 ModelRunner._build_attn_state（v1 attention 状态机）按 seq_lens 与 num_scheduled_tokens 关系挑 AscendAttentionState 的路径。根因：PrefillNoCache 假定注意力只算当前段 token、不回读物理 KV cache，而 CLA 共享层本层不写 KV 却必须读目标层写入的 cache，用本层 token 分布推断 cache 命中状态对共享层不成立。修法：在 _build_attn_state 入口加短路分支——只要 self.shared_kv_cache_layers is not None 就直接 return AscendAttentionState.ChunkedPrefill（ChunkedPrefill 路径会读分页 KV cache，与 FIA/npu_fused_infer_attention_score 带 block_table 从块池读非连续 KV 一致），绕过后续基于 seq_lens 相等性的状态选择。须与「共享层跳过 KV cache 写入」「共享层 KV 张量别名到目标层物理块」两处配套改动一起才闭合。correctness 由 aclgraph vs eager e2e 输出一致性测试验证，源未给性能数字。约束（一律强制 ChunkedPrefill 的粗粒度、依赖 shared_kv_cache_layers 字段）为该 vLLM-Ascend 参考实现取的折中，非 CLA 语义必然。
tags:
- task.debugging
- topic.attention
- topic.kv_cache
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/4138
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 跨层 KV-sharing（CLA）模型在昇腾上误选 PrefillNoCache：共享层要读别层写入的 KV cache，须强制 ChunkedPrefill

## 信号（现象）

在昇腾 backend 上跑**跨层 KV-sharing（cross-layer attention, CLA）**模型——即某些注意力层不自己写 KV cache、而是复用（读取）另一目标层写入的同一份 KV cache——时，共享层的注意力状态被选成了 `PrefillNoCache`（或其它「假定本层无历史 cache 命中」的状态），结果共享层拿不到目标层写入的历史 KV，输出与参考实现（eager / GPU）对不上。

判断自己是否落在本页范围内：

- 模型带跨层 KV 复用（配置里存在「某层共享另一层 KV cache」的映射，如 `shared_kv_cache_layers` / CLA 结构；gemma-3n 属此类）。
- 症状是**正确性**问题（共享层读到空/错 cache），不是显存或性能问题。
- 发生在昇腾 v1 attention 状态机按 `seq_lens` 与 `num_scheduled_tokens` 关系挑 attention state 的路径上。

若模型每层都自写自读 KV（普通 MHA/GQA/MLA，无跨层共享），不在本页范围。

## 触发条件

昇腾 backend 的注意力状态选择逻辑（vLLM-Ascend 的 `ModelRunner._build_attn_state`，即 v1 attention 状态机）会依据一个 batch 内 `seq_lens` 与 `num_scheduled_tokens` 的关系，在 `PrefillNoCache` / `ChunkedPrefill` / decode 等 `AscendAttentionState` 之间做选择。这套判据的隐含前提是：**每个注意力层的 KV cache 命中状态可由该层本次调度的 token 情况推断**。

跨层 KV-sharing 打破了这个前提：共享层本次不写 KV，却要去读**目标层**早先写入的那份 cache。于是即便共享层本次「只处理当前 prompt token、看起来无历史」，常规判据仍可能选到 `PrefillNoCache`——而 `PrefillNoCache` 这条计算路径不会去读物理 KV cache，语义与「共享层必须读别层 cache」直接冲突。

## 根因

`PrefillNoCache` 假定注意力只算当前这段 token、无需回读历史 KV cache；而 CLA 共享层的语义恰恰是「本层不写、但必须读目标层写入的 KV cache」。用「本层是否写了 cache / 本次 token 是否覆盖全序列」来推断 attention state，对共享层不成立——需要读 cache 的层被误判成不需要读 cache 的状态。

`ChunkedPrefill` 这条路径会读取（分页）KV cache，因此对「本层没写但要读一份既有 KV」的共享层，是语义正确的落点。这与昇腾 [fused-infer-attention-score](../../concepts/kernels/fused_infer_attention_score.md)（FIA）带 `block_table` 从块池读非连续 KV 的分页读路径是一致的——共享层需要的正是「带历史 cache 读」的注意力，而非「无 cache 纯当前段」的注意力。

## 修法

在昇腾 attention 状态选择逻辑（`_build_attn_state`）**入口处加短路分支**：只要模型带跨层 KV-sharing，就统一按 `ChunkedPrefill` 处理，绕过后续基于 `seq_lens` 相等性的状态挑选。

```python
def _build_attn_state(self, ...):
    if self.shared_kv_cache_layers is not None:
        # sharing kv across layers need to read the kvcache,
        # directly return chunked prefill in this scenario
        return AscendAttentionState.ChunkedPrefill
    # ... 常规基于 seq_lens / num_scheduled_tokens 的状态选择
```

修法的核心判据：**「本层需不需要读 KV cache」不能只看本层本次的 token 分布，跨层共享会让某层在无本地写入的情况下仍必须读 cache；此时应强制走会读 cache 的注意力状态（ChunkedPrefill），而非按局部 token 情况推断出的 PrefillNoCache。**

这个 attention-state 短路只是 CLA 昇腾适配的一环，须与另外两处配套改动一起才正确（否则共享层的 KV 读/写仍不闭合）：

- **共享层跳过 KV cache 写入**——共享层不产生自己的 KV，不应写块池，避免覆盖/污染目标层的 cache。
- **共享层张量别名到目标层**——把共享层的 KV cache 张量别名（alias）到其目标层的物理 cache，使它读到的正是目标层写入的那份（参见 [kvcache-offload](../../concepts/techniques/kvcache_offload.md) 对 KV cache 物理块管理的讨论；此处是「让多层指向同一物理块」而非搬移到 host）。

### correctness 验证

以 aclgraph 与 eager 两条执行路径跑同一 CLA 模型（gemma-3n），比对端到端输出一致性（e2e output consistency）。共享层能读到目标层写入的 KV、输出与 eager 对齐，即修复到位。

## 参考实现及其约束

- 参考实现：vLLM-Ascend backend 的 `vllm_ascend/worker/model_runner_v1.py` `ModelRunner._build_attn_state`，用 `self.shared_kv_cache_layers is not None` 作门控、直接 `return AscendAttentionState.ChunkedPrefill`；该参考实现以 gemma-3n 作为 CLA 模型验证正确性。
- **约束是该实现的、不是技术本身的**：
  - 「一律强制 ChunkedPrefill」是**粗粒度**处理——只要模型带任一跨层共享层，整个状态机就被统一按 ChunkedPrefill 走，不再对非共享层做精细的 PrefillNoCache/decode 优化选择。这是为正确性放弃部分状态特化，属该参考实现取的折中，非 CLA 语义的必然。
  - 触发门控依赖 `shared_kv_cache_layers` 这个 vLLM-Ascend/vLLM 侧配置字段存在且非 None；换框架时对应的是「模型是否声明了跨层 KV 复用」这一信息，字段名不通用。
  - 源未给性能数字；正确性由 aclgraph vs eager e2e 一致性测试保证。范围限定 vLLM-Ascend 该 backend 的 CLA KV-sharing 分支行为，不外推到其它状态机实现。

## 相关经验

- 分页 KV cache 的读/写算子契约与块管理见 [昇腾 Paged-Attention KV cache：block_table/slot_mapping 同 vLLM](../../optimizations/experience/rules/ascend_paged_attention_kv_cache.md)——CLA 共享层最终读的正是这套分页物理块。

## Evidence

- `diff 事实`（merge sha 449f8f65a780f7d8fe519c1b6e7ddb1f33d8c6ac）：`vllm_ascend/worker/model_runner_v1.py` 的 `_build_attn_state` 入口新增 `if self.shared_kv_cache_layers is not None: return AscendAttentionState.ChunkedPrefill`，代码注释直述「sharing kv across layers need to read the kvcache, directly return chunked prefill」。根因（共享层需读 cache、故不能走 PrefillNoCache）由该注释直接给出。correctness 由 aclgraph vs eager e2e 一致性测试保证；源未给性能数字。
- 溯源下探：
  - [vllm-ascend-pr-4138-kv-sharing-support-kv-sharing-feature-in-cla-models](https://github.com/vllm-project/vllm-ascend/pull/4138)
