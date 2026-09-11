---
type: Runbook
title: 图模式 padding 尾段残留 position 经 split-fuse mask 流入 GatherV3 越界崩溃
description: >-
  在 vLLM-Ascend V1 图模式的 split-fuse/chunked-prefill 路径中，持久复用的 position
  buffer 只更新当前 batch 的有效前缀，padding 尾段会残留上一 batch 的脏索引。当这些值被用于
  索引外部 attention mask 时，可偶发触发 GatherV3 越界断言和 AIV vector core exception；
  eager、V0 及内部构造 mask 的 CUDA 路径不属于该签名。修复是在拷贝有效 position 前，对
  positions[total_num_scheduled_tokens:num_input_tokens] 执行 zero_()。通用边界是：图模式固定形状、
  持久 index buffer 与外部 mask 索引同时存在时，每个 batch 都必须覆盖或清零 padding 区。
tags:
- task.debugging
- topic.attention
- topic.kv_cache
- topic.graph_execution
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/issues/1731
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/issues/1115
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 图模式 padding 尾段残留 position 经 split-fuse mask 流入 GatherV3 越界崩溃

## 信号（现象）

在昇腾 NPU 上、以图模式（ACL graph / aclgraph，`enforce_eager=False`）运行 LLM 推理时，**偶发**（sporadic、hard-to-reproduce）崩溃，报错签名是 `GatherV3` 算子的 host 侧边界断言 + device 侧 AIV vector core exception：

```
[ASSERT] [CANN_VERSION : 8.1.RC1] .../ascendc/gather_v3/gather_v3_base.h:137:
  Assertion `(0 <= val && val < this->gxSize_)' Index 596 out of range [0 596) !
EZ9999: ... there is an aivec error exception ...
fault kernel_name=GatherV3_..._high_performance_80330
rtStreamSynchronizeWithTimeout ... reason=[vector core exception]
synchronize stream failed, runtime result = 507035
```

即 `GatherV3` 收到的某个 index 落在合法区间 `[0, gxSize_)` 之外（如 596 越过 `[0,596)`、308 越过 `[0,273)`、211 越过 `[0,211)`），触发算子内建边界 assert，整个 stream 报 vector core exception。

边界判据：
- 崩溃发生在**图模式**下（`enforce_eager=False`，走 aclgraph）；关掉图模式跑 eager（或用 V0 引擎）则不复现——这是判断该失败签名的关键分水岭。
- 崩溃是**偶发**的：同一 benchmark 可能第一次运行到中途即崩、重跑一次却全程通过，与「上一批遗留的脏索引这次是否恰好越界」相关。
- 报错落在 `GatherV3`，且该 Gather 用于以 position 索引外部构造的 **attention mask**（split-fuse / chunked-prefill 路径）。与 position→mask 索引无关的 `GatherV3` 越界不属该签名。

## 触发条件

- **框架路径**：vLLM V1 引擎在昇腾上跑（vllm-ascend），走 aclgraph 图模式；V0 引擎与上游 CUDA 路径不复现。
- **算子路径**：split-fuse attention（chunked-prefill 场景）需要**外部显式传入** attention mask，mask 由 `position` 张量索引构造（`get_splitfuse_attn_mask`），该索引下降为 `GatherV3`。
- **buffer 复用**：`position` 是跨 batch 复用的持久 device buffer；图模式的 padding 逻辑使 `num_input_tokens ≥ total_num_scheduled_tokens` 恒成立，尾段 `positions[total_num_scheduled_tokens:num_input_tokens]` 是 padding 区。
- **触发规模无关但需 padding 非空**：CANN 8.1.RC1；复现见于 bf16、tp=1/多卡、`max_seq_len=16384/32768`、`enable_prefix_caching=True`、`chunked_prefill_enabled=True`。维护者判断图模式下所有模型「应该」都有概率触发，倾向认为非某模型专属。

## 根因

图模式为保持输入形状稳定（避免重编译），每个 batch 把 token 张量 pad 到固定长度：`num_input_tokens` 始终 ≥ 本批实际的 `total_num_scheduled_tokens`，尾段 `[total_num_scheduled_tokens:num_input_tokens]` 是 padding 区。

问题出在**持久 position buffer 的 padding 尾段没有被本批覆盖**：拷入新一批有效 position 时只写了 `[:total_num_scheduled_tokens]`，尾段仍保留上一批遗留的 **stale/dirty position 值**。这些旧值可能超过当前 batch 的 attention mask 维度。

昇腾特异性是失败暴露的关键：
- 上游 vLLM（CUDA）路径里，split-fuse mask 由算子内部用其它参数构造，这些 padding 尾段的残留值**不外露**，因此上游/V0 不触发。
- 昇腾的 split-fuse attention 需要**外部显式传入 mask**，于是 padding 尾段的残留 position 被真的拿去索引 mask——当残留值越过 mask 维度，作为 index 传给 `GatherV3` 就撞上算子边界检查失败。

因此这是一个**图模式 padding + 持久 index buffer 复用 + 外部 mask 索引**三者叠加才暴露的隐蔽越界，而非模型逻辑或数值精度问题；偶发性来自「残留脏值这一批是否恰好越过 mask 维度」的不确定性。

## 修法

在把有效 position 拷入持久 buffer **之前**，先把 padding 尾段显式清零（一行），保证喂给 `GatherV3` 的每个 index 都落在 mask 合法范围内：

```python
# vllm_ascend/worker/model_runner_v1.py::_process_reqs
self.positions[total_num_scheduled_tokens:num_input_tokens].zero_()
self.positions[:total_num_scheduled_tokens].copy_(
    self.positions_cpu[:total_num_scheduled_tokens], non_blocking=True)
positions = self.positions[:num_input_tokens]
```

`zero_()` 把 padding 区归零到合法的 index 0，覆盖掉上一批的脏值。这是稳定性 / correctness 修复（消除偶发崩溃），不改变有效区语义、无性能收益也无回退风险。

**通用抓手**：任何在昇腾上以「外部 position（或其它 index）索引外部构造的 attention mask」+ 图模式固定形状 padding + **复用持久 index buffer** 的实现，都可能因 padding 尾段残留脏索引撞 `GatherV3`（或其它 Gather 类算子）越界。核对点是——**持久 index buffer 的 padding 区，在每个 batch 是否被显式清零 / 覆盖到合法范围内**；只写有效前缀而不清尾段就是隐患。这是从 CUDA 路径移植时最易漏的一步，因上游根本不把该残留值外露。

### 参考实现及其约束

- **参考实现**：vllm-ascend `vllm_ascend/worker/model_runner_v1.py::_process_reqs` 在 copy 前插入 `self.positions[total_num_scheduled_tokens:num_input_tokens].zero_()`；mask 构造在 `vllm_ascend/attention/attention.py::get_splitfuse_attn_mask`。修复分两支落地：v0.9.1-dev 分支自 v0.9.1rc2 起（merge sha `bf171525f2b3709571cab393e300e0609ecb9006`），main 自 v0.9.2rc1 起（merge sha `2690697caa47ab8daee4083778020ea7c13c16c7`）。
- **约束（属该参考实现、非技术本身）**：`positions` / `positions_cpu` 命名、`_process_reqs` 落点、split-fuse mask 由外部传入这些是 vllm-ascend V1 路径的实现细节；「持久 index buffer 的 padding 尾段每 batch 必须清零」才是可迁移的通用纪律。复现覆盖 Qwen2.5-VL-7B-Instruct、Qwen2.5-7B-Instruct、qwen3-30b-a3b（Qwen3-MoE），维护者判断图模式下所有模型「应该」都有概率触发——模型名是复现样本、不是技术边界。
- **验证 / 回退**：修后在此前 89/200 崩溃的同一 benchmark 上跑到 200/200 通过（源自报的稳定性观测，无独立 before/after 定量复测）。判定修复生效的方式是「同一图模式 + split-fuse + 长 max_seq_len + prefix caching + chunked prefill 配置下不再偶发 `GatherV3` 越界 assert」。

## Evidence

- [vllm-ascend-issue-1731-bug-v1-llm-engine-qwen2-5-vl-7b-instruct-v0-engine](https://github.com/vllm-project/vllm-ascend/issues/1731) — issue（维护者结论 issue resolved，指向 0.9.2rc1）；修复合并态 diff @ merge sha `2690697caa47ab8daee4083778020ea7c13c16c7`（main / v0.9.2rc1，`_process_reqs` 插入 `zero_()` 一行）。
- [vllm-ascend-issue-1115-v0-9-0rc2-faq-feedback](https://github.com/vllm-project/vllm-ascend/issues/1115) — issue（报错现场，维护者判断图模式下所有模型「应该」都有概率触发）；修复合并态 diff @ merge sha `bf171525f2b3709571cab393e300e0609ecb9006`（v0.9.1-dev / v0.9.1rc2，2025-06-26 合入）。
- 核心链路（症状 = `GatherV3` 越界 / 根因 = 图模式 padding 区残留 stale position + 昇腾外部 mask 索引 / 修法 = 拷入前 `zero_()` 清零）出自合并态 diff 与 PR 描述给出的根因链；两份 issue 在不同模型上复现同一失败签名，互相印证。
- 静态概念：图模式机制见 [npu-graph-mode](../../concepts/techniques/npu_graph_mode.md)；昇腾 split-fuse / 融合注意力算子路径见 [fused-infer-attention-score](../../concepts/kernels/fused_infer_attention_score.md)。