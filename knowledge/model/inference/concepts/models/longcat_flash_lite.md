---
type: Concept
title: LongCat-Flash-Lite
description: 当前 Lite 双子层、独立N-gram词表、packed/PA缓存、已落地Prefill SP、自动MC2回退与Prolog/多流边界。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/models/modeling_longcat_flash_lite.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/models/configuration_longcat_flash_lite.py
  role: constraint
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/agentic/optimization_report_ep.md
  role: supporting
created_at: '2026-04-16T00:00:00Z'
updated_at: '2026-10-29T13:59:24Z'
platforms:
- a2
- a3
---

# LongCat-Flash-Lite

## 结构

Lite约69B参数，包含14个双子层Decoder；每层两段MLA、两段Dense MLP，以及将MoE输出加到第二子层的shortcut。MLA配置q_lora1536、kv_lora512、nope128/rope64、32heads；MoE为256 routed加128 identity专家、top12。Dense中间维6144与专家中间维1024分属不同模块。

主词表与LM Head为131072；当前EP报告已修正旧155136记法，不再保留该旧文档冲突。N-gram使用12张独立大表，ngram_vocab_size_ratio×vocab_size决定子表规模，不改变主词表。

## 当前实现

全链路采用packed-token布局。MLA缓存只存512+64维latent，由共享ModelCacheInfo/CacheEntry分配和绑定；14层双MLA形成28个逻辑cache层。N-gram滚动窗口为persistent=False的buffer，在权重处理阶段按每DP rank batch预分配，Decode原地更新；packed Prefill按文档段边界更新上下文。

当前EP Prefill已实际实现is_sp与ReduceScatter/AllGather，触发条件attn_tp>1且attn_dp>1。旧“报告有SP但源码没有”的缺口已不成立。A2 MC2每rank专家上限24，超出时当前代码自动选择double routing；不能把A3的EP数字泛化到A2同路径。

Decode当前直接进入MLA Prolog，没有旧enable_mla_prolog开关。多流MoE overlap是Decode可选优化，现存流helper为GE scope，不应因框架支持npugraph_ex就推导该多流组合已验证。

## 部署与来源观测

- [当前部署](../../guides/models/longcat_flash_lite_deployment.md)
- [N-gram入图案例](../../optimizations/cases/longcat_lite_ngram_graph_host_gap.md)
- [TP/Prolog来源观测](../../optimizations/benchmark_observations/longcat_lite_a3_prolog_source_benchmark.md)
- [EP/W8A8来源观测](../../optimizations/benchmark_observations/longcat_lite_ep_source_observations.md)

性能报告中的BF16 token分歧需要任务精度验收，本次未执行模型。


## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/README.md)（primary）
- [modeling_longcat_flash_lite.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/models/modeling_longcat_flash_lite.py)（implementation）
- [configuration_longcat_flash_lite.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/models/configuration_longcat_flash_lite.py)（constraint）
- [optimization_report_ep.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/agentic/optimization_report_ep.md)（supporting）
