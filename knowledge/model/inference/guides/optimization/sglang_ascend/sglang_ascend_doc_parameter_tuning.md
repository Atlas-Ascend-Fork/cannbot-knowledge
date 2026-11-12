---
type: Guide
title: SGLang Ascend 调参：按角色预算内存、通信与图覆盖
description: 以DeepSeek-V3.2 A3配方为参照，串联TP/AttentionDP/CP、DeepEP容量、图batch、投机和缓存的决策顺序，保留兼容矩阵的部分/未知状态。
tags:
- task.optimization
- topic.model_serving
- topic.parallelism
- topic.memory
- topic.graph_execution
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/optimization/parameter_tuning.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/deepseek_v3_2.mdx
  role: constraint
created_at: '2026-11-08T11:50:28Z'
updated_at: '2026-11-08T11:50:28Z'
platforms:
- a3
---

# SGLang Ascend 调参：按角色预算内存、通信与图覆盖

## 先固定部署判断

本任务以来源选取的DeepSeek-V3.2 A3场景为参照，先确认模型、精度、Prefill/Decode角色、输入长度、并发、延迟目标和资源，再调整性能参数。参数表参考值不是所有模型或所有Ascend产品的默认推荐。系统电源、NUMA、swappiness与CPU affinity的设置用于降低主机抖动，修改前后应保留同负载基线与可回退配置。

## 内存、通信和并行分开预算

mem-fraction-static控制静态权重/KV预算占比，调低给激活和运行时留余量，调高可能增加KV容量。expandable_segments改变缓存分配器行为；只有大pinned host池或HiCache出现分配问题时再评估pin_memory_expandable_segments，两者都不能保证消除所有OOM。

多节点HCCL_SOCKET_IFNAME/GLOO_SOCKET_IFNAME必须与实际网络一致；PD须配置一致可达MemFabric store。DeepEP HCCL缓冲与KV预算是不同资源，P的批量通信和D的小batch可使用不同大小，不凭某份表的“host memory”措辞推定实际缓冲归属。DEEPEP与普通HCCL组的变量分层须按框架实现核对。

区分模型副本DP与TP组内Attention DP；来源当前说明副本DP>1不与Attention DP组合。AttentionDP应整除TP，MoE EP切专家，dense TP和LM Head策略另核对。当前Ascend文档写attn-cp-size须等于tp-size；这不是旧QwenNext补丁CP+TP切分的参数契约，通用[CP规则](/model/inference/optimizations/rules/long_seq_prefill_context_parallel.md)与模型配方应交叉阅读。

## Prefill与Decode配置顺序

- Prefill先检查chunked-prefill-size与max-prefill-tokens、prefill并发、prefix命中。专用长序列P配方关闭chunking和NPU graph；不能由这个配方推出所有Prefill都不适合图或chunking。无共享前缀的RANDOM负载关闭RadixCache，真实多轮聊天需另测。
- Decode先观察每rankbatch分布，再选显式图batch列表或max-bs。图覆盖增加捕获时间与显存；高全局并发不能直接当作每rank图batch。仅在请求分布均衡时考虑SGLANG_SCHEDULER_SKIP_ALL_GATHER，否则保留同步调度以免失衡。
- DeepEP normal/low_latency分别针对批量P与小batchD，auto按阶段选择。每rank LL dispatch容量要覆盖真实候选token数，投机下按每rank请求与draft token数预算；文档上限1024只表示该版本的框架说明，不覆盖外部Kernel的更窄范围。

## 投机、融合与兼容性

NEXTN使用内置MTP，EAGLE3使用外部draft；候选步数、topk、总draft tokens分别影响计算、接受率与容量。overlap-plan-stream是spec-v2准备流，普通overlap schedule是CPU调度/设备计算重叠，不是同一开关；前者与LoRA不兼容。默认target-only验证可处理linear/tree，classic rejection受linear和topk1限制。

MLAPO只用于相应MLA预处理，FIA NZ要求与MLAPO配套；共享/路由专家多流与索引器多流的具体路径不同。AG_AFTER_QLORA、AIV通信、EPLB、NZ权重格式均需模型与实际Kernel支持，不把名称含“优化”当作收益证据。来源EPLB说明支持deepep、不支持ascend_fuseep；NZ与某些动态权重功能可能冲突。

兼容矩阵包含full、partial、no、unknown四态：NPU graph、chunked prefill和多种特性多为partial；CP+DP LM Head、MLAPO/EPLB等有unknown。未知不能当兼容；矩阵没有给出某一产品/软件组合的独立验收。先退回同版本基础配置，逐项启用并分别比较TTFT、TPOT、吞吐、KV容量与精度；仅复现整体配方不能对单个开关归因。本次未修改主机、执行服务或基准。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/optimization/parameter_tuning.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/optimization/parameter_tuning.mdx)（primary）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/deepseek_v3_2.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/deepseek_v3_2.mdx)（constraint）
