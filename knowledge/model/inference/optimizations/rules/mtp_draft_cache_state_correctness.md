---
type: Optimization
title: MTP 缓存：按实际层声明，按接受前缀推进
description: 依据当前缓存声明与MTPWorker说明层数、接受前缀和请求边界，并区分 SGLang GDN 的状态提交语义。
tags:
- task.optimization
- topic.model_architecture
- topic.attention
- topic.graph_execution
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/mtp_worker.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/base_speculative_worker.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/README.md
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/ops/gated_delta_net/recurrent_gated_delta_rule/op_kernel/recurrent_gated_delta_rule.h
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T14:41:22Z'
platforms:
- agnostic
---

# MTP 缓存：按实际层声明，按接受前缀推进

## KV 缓存

当前 Executor 的主模型与 draft 分别报告 `ModelCacheInfo`，统一缓存管理器据实际层及 CacheEntry 分配和绑定。R1 的 MTP `get_cache_info` 遍历 `self.model.layers.values()`，层数是实际预测层数，不是顺序调用次数 `next_n`；旧 runner 的按草稿步分槽与换槽规则不再适用。

MTPWorker 将种子与候选拼成 `next_n+1` 桶。验证得到最长匹配前缀后，后续 draft 输入按接受索引选择种子，推进 `kv_len` 并重新计算 position、slot mapping、Q/KV 的序列元数据。必须追踪到算子实际消费的槽与长度，单看缓存分配份数不能证明正确。

Prefill packed 序列的左移不能把一条请求尾部与下一条请求串联：当前代码在各请求累计长度减一处放对应主模型 next token。CP 则另按 global_valid_indices 和全局请求尾部处理。

## 递归状态

Qwen3-Next 的 SGLang 路径是另一套实现。GDN kernel 根据 `num_accepted_tokens` 选择上轮起始槽，并存储本轮验证 token 的中间 SSM 状态；框架在接受结果确定后选择下一轮持久状态/索引。不能把“只提交接受前缀”全部归给 kernel 内部写回，也不能把全部草稿状态无条件作为最终状态。Conv 滑窗也必须按接受前缀推进。

该 SGLang 集成当前 MTP 与图模式、C8、PD 分离不兼容，且需要融合 GDN；这些限制不能推广到 Executor R1，后者有图模式+MTP 的配置。Qwen3.5 当前明确 `next_n=0`，不能由共享 GDN 结构推导它支持投机。

## 验证

覆盖零、部分、全部接受以及 EOS/长度截断，多请求不能互相污染。与关闭投机的确定性输出逐 token 对齐；检查持久状态、临时态、block table、slot mapping 和位置共同回到接受前缀。相关接入见[MTP 指南](../../guides/integration/mtp_speculative_decode_model_onboarding.md)，分片调度见[Prefill 记账](mtp_cache_and_microbatch_prefill_bookkeeping.md)。

## Evidence

- [mtp_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/mtp_worker.py)（primary）
- [base_speculative_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/base_speculative_worker.py)（implementation）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py)（implementation）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/README.md)（implementation）
- [recurrent_gated_delta_rule.h](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/ops/gated_delta_net/recurrent_gated_delta_rule/op_kernel/recurrent_gated_delta_rule.h)（implementation）
