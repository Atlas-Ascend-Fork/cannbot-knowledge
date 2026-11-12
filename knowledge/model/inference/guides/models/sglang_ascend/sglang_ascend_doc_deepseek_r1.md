---
type: Guide
title: SGLang Ascend DeepSeek-R1：A3量化、PD拓扑与NEXTN配置
description: 融合v0.5.18教程、W4A8/W8A8性能配方与旧DeepSeek例子，区分物理卡/TP设备、图档位和阶段通信，记录可复核性能条件。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/deepseek_r1.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/deepseek_r1.mdx
  role: constraint
- resource: https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/hardware-platforms/ascend-npus/DeepSeek%20Examples.mdx
  role: primary
created_at: '2026-11-08T11:50:28Z'
updated_at: '2026-11-08T11:50:28Z'
platforms:
- a3
---

# SGLang Ascend DeepSeek-R1：A3量化、PD拓扑与NEXTN配置

## 版本、权重和设备计数

本页只将SGLang上游的DeepSeek-R1配方归纳为A3部署任务，不改写[DeepSeek模型机制](/model/inference/concepts/models/deepseek_r1.md)。当前教程与最佳实践均限定SGLang v0.5.18、镜像v0.5.18-cann9.0.0-a3，后续版本未覆盖；不能直接套通用安装页的9.1.0组件组。

R1为671B总参数、37B激活的MoE+MLA模型，支持内置MTP。来源列W4A8权重376GB，最低推荐8×64GB设备（A3物理4卡、TP8）；W8A8为647GB，最低推荐16×64GB（物理8卡、TP16）。这是最低装载配置，最佳实践的P/D资源另算。A3物理一张卡为两个die，表中Cards不能直接当TP size。

## 按阶段选择配方

共同入口为--device npu、--attention-backend ascend、--quantization modelslim。MLAPO与FIA NZ配套，SGLANG_SET_CPU_AFFINITY、streams和分配器配置为该配方的一部分；先复现同配置，再独立消融，不能把整体吞吐归因某一个开关。

- W4A8混部使用TP16、DP16、DeepEP auto、DP LM Head、NEXTN(steps3,topk1,draft4)，显式decode图档位4/8/12/14，最大运行请求224。Normal长序列按每轮1024、轮数10分批传输，通信缓冲2000MB。这是8物理卡的配方，不是前述最低TP8装载方案。
- W4A8 1P1D分离在P用TP16/DP8、DeepEP normal与更大的prefill预算；D用TP16/DP16、low_latency、NEXTN(2,1,3)、decode图档位至26和最大416请求。P/D共用MemFabric store，router的bootstrap须与P配置一致。
- W8A8低时延配方为2P1D、32物理卡：每个P实例单节点TP16/DP2，D跨两节点TP32/DP16或DP8，按输入长度调整；D图档位2/4/6、并发32，和吞吐配方的1024并发不能混用。
- W8A8吞吐配方另用ascend_fuseep，P与D的SGLANG_NPU_FUSED_MOE_MODE分别2/1，D的LM Head TP为8，并配置更大的图覆盖与并发。这与旧独立docs中“fuseep只用于PD Decode”的说明存在阶段差异：本卡只记录该固定新配方，不把旧限制或新脚本任一方泛化为所有版本的可用性。

通信预算、max-total-tokens、mem-fraction-static、dispatch容量和每rank图batch须成组核对。max-running-requests超过实际图档位×DP覆盖时可能退化，旧例子对此有提示；不能只提高并发而不测图命中与显存。

## 上游性能记录的限定条件

下列TPOT均为来源自报，不是本次测量；硬件为A3，软件固定上述镜像，数据为RANDOM，输入/输出长度明确。

| 配方 | 输入/输出 | 并发、prompt数、速率 | 来源TPOT |
| --- | --- | --- | --- |
| W4A8 1P1D，16物理卡 | 3584/1536 | 416、1664、24req/s | 50ms |
| W4A8混部，8物理卡 | 3500/1500 | 224、896、未指定速率 | 50ms |
| W8A8 2P1D低时延，32物理卡 | 3500/1500 | 32、32、16req/s | 20ms |
| W8A8 2P1D吞吐，32物理卡 | 3584/1536 | 1024、7168、40req/s | 50ms |
| W8A8 2P1D，32物理卡 | 3500/1024或3900/1024 | 32、32、16req/s | 19ms |
| W8A8 2P1D，32物理卡 | 6000/1600 | 32、32、16req/s | 20.5ms |

来源未给重复轮数、方差、独立基线与warmup细节；TPOT不是TTFT或端到端总时延，不能跨不同并发与量化直接算优化倍率。

## 历史差异、验证和回退

旧sgl-docs页面标题写DeepSeek-V3但权重链接实际指R1，且示例用CANN8.5路径、SGLANG_ENABLE_SPEC_V2和旧--cuda-graph-bs参数。保留其P normal/D low_latency、GSM8K 5-shot/200题/parallel32的验收思路，不将该旧整条命令直接应用于v0.5.18。旧NIC示例中的lo同样不代表真实跨节点可达网络。

验证先固定正确模型权重、量化和P/D拓扑，检查router请求、NEXTN接受率、精度与图覆盖，再按同一随机长度/并发/请求率采集TTFT、TPOT、吞吐。回退时恢复完整的非投机/基线通信及镜像组合，不只关闭单个融合变量。本次未启动服务、执行评测、安装镜像或运行上游代码。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/deepseek_r1.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/deepseek_r1.mdx)（primary）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/deepseek_r1.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/deepseek_r1.mdx)（constraint）
- [sgl_docs：docs/hardware-platforms/ascend-npus/DeepSeek Examples.mdx](https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/hardware-platforms/ascend-npus/DeepSeek%20Examples.mdx)（primary）
