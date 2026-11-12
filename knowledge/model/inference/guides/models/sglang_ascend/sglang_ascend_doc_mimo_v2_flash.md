---
type: Guide
title: MiMo-V2-Flash 在 A3 的 PD 与分层 EAGLE 配方
description: 区分 MiMo W8A8 的容量起点、实际 P/D 资源、DP 选路、SWA 预算与 TTFT/TPOT 负载。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/mimo_v2_flash.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/mimo_v2_flash.mdx
  role: constraint
created_at: '2026-11-08T11:58:59Z'
updated_at: '2026-11-08T11:58:59Z'
platforms:
- a3
---

# MiMo-V2-Flash 在 A3 的 PD 与分层 EAGLE 配方

## 固定版本与资源

教程限定SGLang v0.5.18、CANN9.0 A3镜像。W8A8 checkpoint约311.5GB，单实例容量起点TP8（A3的4物理卡）；最佳实践PD P端TP8/DP2、D端TP16/DP2，消耗的资源不能用容量起点替代。教程导航中“24P”与最佳实践表的“16卡”不一致，复现应以实际进程、device分配和并行组核对资源，不能自行修正来源口径。

## P/D 角色

P使用chunk8192、SWA/full tokens ratio0.3、禁用Radix与graph，并配置`SGLANG_DISAGGREGATION_FORCE_QUERY_PREFILL_DP_RANK=1`以配合P端DP。D使用DP attention/DP LM head、DeepEP low_latency、EAGLE steps3/topk1/draft4，额外启用multi-layer-eagle。来源明确关闭overlap plan stream；不能直接套用其他模型开启该开关的配方。P/D的dispatch上限、buffer和图batch各自不同。

router使用PD、cache_aware及mini-lb，P bootstrap8998；长bootstrap/waiting超时只保留该示例设置，不能当通信故障的根治方法。先检查实际P DP rank、KV传输和MTP加载，再对请求链路做验收。

## 上游指标

来源报告W8A8 INT8、A3 PD的16K/32K输入：output1时TTFT5s；output1000时TPOT20ms。TTFT命令均128请求、并发64、request-rate0.4，TPOT16K为128请求/并发32，32K为192请求/并发48、rate=inf，RANDOM定长seed1。两类负载测量目标不同，不能把output1的TTFT和长生成吞吐混为一项改善；来源缺重复次数、误差及完整warmup，本次没有执行。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/mimo_v2_flash.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/mimo_v2_flash.mdx)（primary）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/mimo_v2_flash.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/mimo_v2_flash.mdx)（constraint）
