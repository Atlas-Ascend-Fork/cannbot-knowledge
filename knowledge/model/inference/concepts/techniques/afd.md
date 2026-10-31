---
type: Concept
title: Attention-FFN Disaggregation (AFD)
description: AFD 将 Attention 与 FFN 放在独立节点，通过收发交换中间结果，使两侧计算资源可以分别配置。是否减少等待取决于计算、通信与汇合依赖；该机制本身不保证时延收益。
tags:
- task.optimization
- topic.attention
- topic.mixture_of_experts
- topic.kv_cache
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/README.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py
  role: implementation
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T13:46:35Z'
platforms:
- a3
---

# Attention-FFN Disaggregation (AFD)

## Summary

AFD 将 Attention 与 FFN 放在独立节点，通过收发交换中间结果，使两侧计算资源可以分别配置。是否减少等待取决于计算、通信与汇合依赖；该机制本身不保证时延收益。

## Mechanism

### 出发点：控核的副作用

同卡多流控核让每条计算路径只能使用部分核；分离后可分别分配资源。具体核数耗时统一见[来源观测](../../optimizations/benchmark_observations/longcat_a3_afd_source_benchmark.md)，不在机制卡重复结果表。

### AFD 部署结构

使能 AFD 技术前后的网络结构示意图：

![LongCat-Flash 使能 AFD 前后对比](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/figures/w_afd.png)
*来源：[`docs/models/longcat-flash/figures/w_afd.png`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/figures/w_afd.png)（cann-recipes-infer @ 944d2d3）*

Attention 和 MoE 独立部署后：

![AFD Attention / MoE 独立部署](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/figures/afd_deploy.png)
*来源：[`docs/models/longcat-flash/figures/afd_deploy.png`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/figures/afd_deploy.png)（cann-recipes-infer @ 944d2d3）*

### 计算流图

固定 LongCat 优化指南描述的 AFD 实现中，**Send/Recv 跨节点通信走 SDMA、不占用 Vector 核**，因此无需沿用本地 MoE 计算流的控核方式。下面是指南的设备侧编排说明；实际流映射和重叠仍需按所用图后端核对。

计算流上，在 Attention 节点上：第一个 LayerNorm(LN) 算子的结果，一方面通过 Send 算子发送到 FFN 节点上；另外一方面，同时送给下一个算子完成后续的计算操作。在 Send 算子完成发送动作后，会同时通过 Recv 算子等待并接收从 FFN 节点发送回来的数据。Attention 节点上的 Send/Recv 算子在 Stream1 上和主流 Stream0 上的计算算子进行 overlap，达到通信计算隐藏的目的。

![Attention / FFN 节点计算流 overlap](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/figures/attn_ffn_stream.png)
*来源：[`docs/models/longcat-flash/figures/attn_ffn_stream.png`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/figures/attn_ffn_stream.png)（cann-recipes-infer @ 944d2d3）*

同理，FFN 节点作为服务端，任务执行时图上第一个是 Recv 算子，它一直等待直到 Attention 节点通过 Send 算子发数据过来。当前 FFN 节点接收到数据后，会进行 Router/Dispatch/MoE-GMM/Combine 等操作，最后再通过 Send 算子将数据发回 Attention 节点。

### FFN 侧瓶颈

分离后仍可能受 FFN 侧限制；实现分析见[AFD 案例](../../optimizations/cases/longcat_a3_afd_stream_pairing.md)，诊断由[FFN 等待 Runbook](../../runbooks/performance/afd_ffn_side_bottleneck_prefetch.md)维护。

## 当前源码边界

当前使用 model_config.custom_params.enable_afd，偶数 world_size 分成 FFN/Attention 两半，CommManager 负责两半的业务组。npugraph_ex Decode 在本地计算后、相加前接收结果；GE 等路径依所用图调度执行。指南图示表达目标重叠，不代替实际时间线。多流、预取和图模式约束见当前部署与案例。

## Applicable Scenarios

- LongCat-Flash ScMoE 结构的 Decode 阶段，对 TPOT 有极致要求时
- 可接受 Attention / MoE 两种 Instance 类型同机柜跨节点部署的运维复杂度
- 目标：把 Attention 算子耗时恢复到不控核水平，同时通过 Send/Recv overlap 掩盖跨节点通信

## Constraints

- 固定 LongCat 版本采用 **1:1 配对（M == N）**，不由此限制其他 AFD 实现。
- 该版本的 `enable_multi_stream` 配置注明在 AFD 场景不生效；这限制的是原本地计算多流开关，不能据此判断设备侧通信是否重叠。
- FFN 侧成为瓶颈时可能出现 EVENT_WAIT 拖尾，预取是来源提供的排查方向，须验证净收益，不能保证消除所有等待。
- 本卡只确认固定来源中的 LongCat-Flash 实现（配置：`longcat_flash_densetp8_ep64_gegraph_mtp2_eplb_afd_w8a8.yaml`、当前两半 rank 配置）。

## Known Results

完整数据见[LongCat A3 来源观测](../../optimizations/benchmark_observations/longcat_a3_afd_source_benchmark.md)；没有跨模型性能保证。

## 多流优化（case pattern）

[LongCat 收发配对案例](../../optimizations/cases/longcat_a3_afd_stream_pairing.md)维护实现；[AFD 规则](../../optimizations/rules/afd_attn_ffn_disaggregation.md)维护决策，[FFN 拖尾 Runbook](../../runbooks/performance/afd_ffn_side_bottleneck_prefetch.md)维护诊断。

## Evidence

- [longcat_flash_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md)（primary）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/README.md)（supporting）
- [modeling_longcat_flash.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py)（implementation）

## Links

- [longcat-flash](../models/longcat_flash.md)
- [moe-multi-stream](moe_multi_stream.md)
- [weight-prefetch](weight_prefetch.md)
- [superkernel](superkernel.md)
- [atlas-a3](../platforms/atlas_a3.md)
