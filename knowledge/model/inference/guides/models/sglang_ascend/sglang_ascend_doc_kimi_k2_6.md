---
type: Guide
title: Kimi-K2.6 在 A3 的多模态、长输入与共享前缀配置
description: 把 Kimi-K2.6 的固定版本 W4A8/EAGLE3 配方按随机文本、共享前缀和图像负载区分。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/kimi_k2_6.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/kimi_k2_6.mdx
  role: constraint
created_at: '2026-11-08T11:58:59Z'
updated_at: '2026-11-09T04:34:03Z'
platforms:
- a3
---

# Kimi-K2.6 在 A3 的多模态、长输入与共享前缀配置

## 适用起点

教程明确限定SGLang v0.5.18、`v0.5.18-cann9.0.0-a3`，后续版本不在验证范围。W4A8权重约535.91GB，容量起点为A3 TP16、8物理卡/16die；性能方案按负载扩到16物理卡。EAGLE3使用独立draft权重，并指定unquant，不能把内置MTP、NEXTN或其他模型draft替换成同一语义。

## 按输入形态调整服务

文本、多模态命令都显式启用multimodal、`mm-attention-backend ascend_attn`、ascend sampling及kimi_k2推理/工具解析器。服务端拉取图像URL需要网络可达；HTTP200的图片描述只证明基本链路，不能替代视觉精度评测。

64K双节点混部使用TP32/DP32、DeepEP auto、graph batch1、EAGLE3的3/1/4；128K PD中P启用ZBAL、TP16、chunk16384，D启用MLAPO/multistream并配独立draft。64K PD随机输入方案的P显式禁用图和Radix cache；64K共享前缀方案没有这两个开关，保留来源图默认开启的前提。D根据随机与前缀负载分别选择graph和DP。共享前缀方案在P保留Radix cache，随机方案常禁用；这不是一组可混抄的默认参数。

单节点低延迟文本方案TP16/DP16，EAGLE3为4/1/5，prefill-delayer最大delay passes200；吞吐方案把max-running从80提高到208、graph覆盖扩展且delay passes降到50。图像1024²方案为EAGLE3 2/1/3，max-running176、graph覆盖到11；1080p方案也使用2/1/3但并发与buffer不同。模型工作集与调度成组改变，不能归因为单一开关。

## 上游报告与复现条件

以下均为A3 W4A8 INT8来源报告；未报告独立重复次数和误差，本次未跑基准。

| 物理卡/模式 | 输入/输出与负载 | 报告 |
|---|---|---|
| 8混部 | RANDOM3500/1500，并发64/请求256，warmup0，seed1 | TPOT20ms |
| 8混部 | 同长度，并发192/请求768，warmup0，seed1 | TPOT50ms |
| 16混部 | RANDOM64000/1000，并发32/请求32，seed1 | TPOT100ms |
| 16 PD | RANDOM128000/1000，1并发/1请求 | TPOT100ms |
| 16 PD前缀 | 115200共享+12800后缀/1000，1组4请求、并发1 | TPOT100ms，TTFT5s |
| 16 PD | RANDOM64000/1500，1并发/1请求 | TPOT100ms |
| 16 PD前缀 | 57600共享+6400后缀/1500，1组8请求、并发2 | TPOT100ms，TTFT3s |
| 8图像混部 | 单张1024²+文本30/output1024，并发160/请求640，warmup16 | TPOT50ms |
| 8图像混部 | 单张1920×1080+文本30/output256，并发48/请求196，warmup16 | TPOT50ms |

90%是生成数据的共享前缀比例，不保证每个请求实测命中率；首个冷请求、路由与驱逐都会改变命中。不同表行不能直接算缓存、PD或分辨率的独立加速比。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/kimi_k2_6.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/kimi_k2_6.mdx)（primary）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/kimi_k2_6.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/kimi_k2_6.mdx)（constraint）
