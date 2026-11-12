---
type: Optimization
title: DeepEP 在 A3 HCCS 上的上游通信性能观测
description: 保存 4096-token Normal 与 128-token LL 的 EP 规模、通信精度和带宽时延，限定软件身份、计时与重复统计缺口。
tags:
- task.optimization
- task.testing
- topic.parallelism
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/README.md
  role: primary
created_at: '2026-11-09T04:33:52Z'
updated_at: '2026-11-09T04:33:52Z'
platforms:
- a3
---

# DeepEP 在 A3 HCCS 上的上游通信性能观测

## 证据身份与可用范围

固定 sgl-kernel-npu README 报告了 A3 384 SuperPOD 上的 Normal 与 Low-Latency 通信数据。本卡保存该上游自报观测，不把 README 所在 commit 当作实际测量时的代码版本，也不声称本次完成了独立复测。

硬件和网络只明确为 A3 384 SuperPOD、Pure HCCS；具体 CPU、驱动、CANN/Torch/DeepEP 版本、固件、镜像 digest 和测量日期未提供。README 的当前 CI 版本说明不能补作这些历史测量的软件环境。不能推广到 A2 的 RDMA 混合链路、950 或不同 HCCS 拓扑。

## 负载、基线与变体

两组均使用 hidden size 7168、top-8 experts、INT8 dispatch 和 BF16 combine，分别改变 EP 规模。Normal 对应每 batch 4096 tokens，Low-Latency 对应每 batch 128 tokens。来源没有进一步说明 batch 是单 rank 还是汇总口径，也未给出专家 token 分布、各 rank 不均衡程度或是否包含布局准备；复测时必须补齐。

来源比较同一路线的不同 EP 规模，没有提供旧实现、其他硬件或关闭某优化的受控 baseline。Normal 和 LL 的 token 数不同，不能把两张表之间的比值当作切换模式的加速比。

## Normal 带宽

上游将以下行标为 Intranode，带宽列称 Bottleneck bandwidth，单位为 GB/s。本文保留其命名；来源没有给出有效字节量公式、聚合方法或计时边界，不能改写成每卡有效带宽、链路峰值利用率或模型吞吐。

| EP ranks | Dispatch 带宽 GB/s | Combine 带宽 GB/s |
|---|---:|---:|
| 8 | 146 | 125 |
| 16 | 107 | 103 |
| 32 | 102 | 95 |
| 64 | 81 | 91 |
| 128 | 57 | 81 |

## Low-Latency 时延与带宽

| EP ranks | Dispatch μs | Dispatch GB/s | Combine μs | Combine GB/s |
|---|---:|---:|---:|---:|
| 8 | 132 | 58 | 126 | 116 |
| 16 | 139 | 55 | 135 | 109 |
| 32 | 153 | 49 | 151 | 97 |

这是 dispatch 与 combine 分开的通信数字，不是完整 MoE 层、token 或请求延迟。README 特性简介中的 sub-150us 不能解释为全部规模的保证：本表 EP32 的两项均大于 150μs。

## 重复、统计与结论边界

来源没有给出 warmup 次数、测量重复次数、平均值/分位数定义、方差、置信区间或原始 profiler 记录。表中数字是上游报告值，不能作为新环境的性能门槛，也不能由单组数据推出所有 EP 扩展的单调规律。

这些观测可作为同拓扑、同精度和同负载复测的参照。改变 EP、批大小、路由分布、量化格式、通信策略或网络时，需分别测量 dispatch/combine 和端到端 MoE，并记录软件身份、warmup、重复次数及指标公式；确认数据正确性后再评估性能。接口模式和容量限制见[Normal 接口](../../../apis/deepep/deepep_normal_dispatch_combine.md)、[LL 接口](../../../apis/deepep/deepep_low_latency_dispatch_combine.md)与[Buffer 策略](../../../guides/integration/sgl_kernel_npu/deepep_buffer_strategies.md)。
