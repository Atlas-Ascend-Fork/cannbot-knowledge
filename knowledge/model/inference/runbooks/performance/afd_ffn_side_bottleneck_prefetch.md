---
type: Runbook
title: AFD 后 FFN 侧成新瓶颈：Attention 侧 Recv EVENT_WAIT 拖尾 → 对 FFN 侧 MoE-GMM 权重做通信间隙预取
description: AFD 后 FFN 侧成新瓶颈：Attention 侧 Recv EVENT_WAIT 拖尾 → 对 FFN 侧 MoE-GMM 权重做通信间隙预取。在 Attention-FFN 解耦（AFD）部署下（Attention 侧解除控核、计算算子提速后），profiling 里 Attention 侧的 Recv 算子长时间收不到 FFN 侧发回的数据，计算流上出现 EVENT_WAIT 间隙的拖尾。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.memory
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/ffn.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md
  role: supporting
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:24:40Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      model_features:
        all_of:
        - moe
      deployment_topology:
        all_of:
        - afd
---

# AFD 后 FFN 侧成新瓶颈：Attention 侧 Recv EVENT_WAIT 拖尾 → 对 FFN 侧 MoE-GMM 权重做通信间隙预取

## 信号（现象）

在 [Attention-FFN 解耦（AFD）](../../optimizations/rules/afd_attn_ffn_disaggregation.md)部署下（Attention 侧解除控核、计算算子提速后），profiling 里 Attention 侧的 Recv 算子长时间收不到 FFN 侧发回的数据，**计算流上出现 EVENT_WAIT 间隙的拖尾**。

## 触发条件 / 根因

解耦本身会**重排瓶颈**。AFD 让 Attention 侧解除多流控核后，MLA_Prolog/FA/MM/TBMM/QBMM 等算子耗时下降，于是 FFN 侧（Router/Dispatch/MoE-GMM/Combine）反而成为新瓶颈——一侧被优化后另一侧暴露为拖尾源，是解耦部署的通用陷阱。Attention 侧 Recv 等不到 FFN 回传，就在计算流上留下 EVENT_WAIT 拖尾。

## 探针与基线

固定平台、输入、并行组与稳态测量区间，先保存关闭预取的时间线；同时查看 FFN GMM/MatMul、通信区间、Attention Recv EVENT_WAIT 与端到端耗时，确认等待来自 FFN 回传而非其他 rank 故障。

## 修法

以下步骤限定固定 LongCat AFD 的 **Decode** 分支：本层 w2 和跨层 router/w13 预取均由 `not is_prefill` 门控，Prefill 走独立 double-routing 路径。对 FFN 侧访存 Bound 的算子（MoE-GMM、MatMul）做**通信间隙权重预取**（[`npu_prefetch`](../../concepts/techniques/weight_prefetch.md)），尝试利用 Send/Recv 通信间隙隐藏部分访存等待、尝试降低 FFN 侧耗时、缩短拖尾，实际效果须对比 profiling 验证：

- 当前层：router 出结果后预取本层 GMM2(w2) 权重 `npu_prefetch(enable_prefetch, experts.w2_weight.data, router_logits, gmm2_prefetch_size, 0)`。
- 跨层流水：拿到 `gmm2_out` 后预取**下一层** `layers[i+1]` 的 `router.classifier.weight`、`experts.w13_weight`（GMM1）。
- 预取字节数按张量规模换算（`gmm1_prefetch_size = hidden_size*intermediate_size*2*dtype_bit//...` 等）。

## 按实际带宽窗口选择预取

非分离场景里 Stream0 计算耗时与 Stream1 上 Router/Dispatch/MoE-GMM/Combine 耗时相当、**没有好的时间窗口**，故当时只对 QBMM/MLA_Prolog/matmul 预取、对 MoE-GMM 未做；AFD 将 MoE 独立到 FFN 节点后可获得不同的预取窗口；当前非 AFD 代码也有 router 等预取，不能将旧案例选择理解为永久不支持。即**预取哪些权重要看该部署形态下有没有可用的通信/计算间隙，不是无脑全预取**。AFD 下 Attention 侧的权重预取与非分离场景保持一致（QBMM/MLA_Prolog/matmul）。

## 当前 npugraph_ex 路径

当前 FFN 在 npugraph_ex、多流与预取同开时建立专用预取流；router 处触发本层 w2 预取，gmm2_event 控制下一层 router/w13 预取，模型出口等待预取完成事件。GE 使用对应的依赖张量调用。预取调用发生不证明 FFN 拖尾已消除。

## 验证与回退

仅切换预取开关，在同负载下重复记录上述区间并核对输出一致性。成功条件是目标 FFN 热点与 Attention 等待缩短，且端到端有净收益；仅搬动等待或出现带宽争用、输出异常、峰值内存增加导致不稳定，都不能判定成功。逐项调整预取位置/大小，仍劣化时关闭预取恢复基线。这里给出验收方法，未声称本仓已完成设备复测。

## 适用边界

这是 AFD 特有的可复用失败签名——下一个在 MoE 上做 AFD 的 agent 遇到 Recv EVENT_WAIT 拖尾可对号入座、优先补 FFN 侧 GMM 权重预取。参考实现为 LongCat-Flash-560B FFN 节点的 Decode（Atlas A3、W8A8、torchair ge_graph）；不能直接将这些预取步骤推广到 Prefill。

## Evidence

- [ffn.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/ffn.py)（primary）
- [longcat_flash_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md)（supporting）
