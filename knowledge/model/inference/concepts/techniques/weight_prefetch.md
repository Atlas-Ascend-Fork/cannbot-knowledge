---
type: Concept
title: Weight Prefetch (npu_prefetch)
description: 权重预取利用前序计算的带宽窗口提前搬运后续权重，解释缓存与依赖机制；调试规则、LongCat 参数和 AFD 故障入口分别引用规范卡。
tags:
- task.optimization
- topic.attention
- topic.graph_execution
- topic.speculative_decoding
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py
  role: implementation
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T13:45:11Z'
platforms:
- a3
---

# Weight Prefetch (npu_prefetch)

## Summary

该优化提供网络 weight 预取功能，在算子计算的同时，**利用空闲的带宽，提前将一些访存 bound 算子的权重从 HBM 搬运到 L2 Cache 中**，提升算子性能。`npu_prefetch` 技术的详细介绍，请参考 [官方文档](https://www.hiascend.com/document/detail/zh/Pytorch/730/apiref/torchnpuCustomsapi/docs/context/torch_npu-npu_prefetch.md)。LongCat-Flash 通过 `model_config.custom_params.enable_prefetch` 开关使能该优化。

## Mechanism

预取在权重被消费前，把数据从 HBM 搬到 L2，利用前序计算留下的带宽窗口减少后续等待。可搬运字节数由可用带宽与窗口时长共同约束，还受缓存容量、其他访问和依赖顺序影响；不能用固定时间或缓存大小推导通用收益。

![weight prefetch 原理示意](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/figures/prefetch_demo.jpg)
*来源：[`docs/models/longcat-flash/figures/prefetch_demo.jpg`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/figures/prefetch_demo.jpg)（cann-recipes-infer @ 944d2d3）*

## 预取分析与调试流程

[预取窗口与预算规则](../../optimizations/rules/decode_weight_prefetch_ordering.md)维护 profiling 判断、调整和回退。

## LongCat-Flash 的预取位置

[LongCat 实现案例](../../optimizations/cases/longcat_a3_decode_weight_prefetch.md)维护权重定位、开关和消费依赖。

## AFD 下的 FFN 侧预取

[AFD 后 FFN 拖尾诊断](../../runbooks/performance/afd_ffn_side_bottleneck_prefetch.md)维护探针与调整。

## Applicable Scenarios

在明确的实现和负载下存在权重搬运等待时，该机制可用于分析候选窗口。已核验的具体适用范围以规则和案例为准，不从机制本身声明所有 eager、图后端或阶段已验证。

## Constraints

带宽争用、缓存容量及依赖生命周期决定是否有效；参数和调整步骤由规范规则/案例维护。

## Known Results

源文档未给出 `enable_prefetch` 单项 A/B 增益数据。LongCat-Flash 配置 `longcat_flash_densetp8_ep64_gegraph_mtp2_eplb_afd_w8a8.yaml` 中 `enable_prefetch: True` 为 Benchmark 默认值。**单项收益待验证**。

## Evidence

- [longcat_flash_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md)（primary）
- [modeling_longcat_flash.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py)（implementation）

## Links

- [longcat-flash](../models/longcat_flash.md)
- [afd](afd.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [torchair](../frameworks/torchair.md)
- [multi-stream](multi_stream.md)（npu_prefetch 与多流是两类硬件资源重叠；多流控核常叠加权重预取，如 LongCat 副流 MoE + 逐级 npu_prefetch）
