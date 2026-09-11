---
type: Optimization
title: Attention-FFN 解耦（AFD）部署：把 MoE/FFN 剥到独立 rank，Send/Recv over SDMA 解除同卡多流控核约束降 decode TPOT
description: Attention-FFN 解耦（AFD）部署：把 MoE/FFN 剥到独立 rank，Send/Recv over SDMA 解除同卡多流控核约束降 decode TPOT。大规模 MoE 在图模式 decode 阶段遇到 host-bound / TPOT 瓶颈，且现方案是 Attention 与 MoE 同卡、靠多流并行「控核」（limit_core_num 给 Attention 流与 MoE 流分配部分 Cube/Vector 核做流水）来取性能时。控核有固有代价——每条流只能用部分核、算子受算力约束。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/249
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/99
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a3
---

# Attention-FFN 解耦（AFD）部署：把 MoE/FFN 剥到独立 rank，Send/Recv over SDMA 解除同卡多流控核约束降 decode TPOT

## 适用场景

大规模 MoE 在图模式 decode 阶段遇到 host-bound / TPOT 瓶颈，且现方案是 Attention 与 MoE 同卡、靠多流并行「控核」（`limit_core_num` 给 Attention 流与 MoE 流分配部分 Cube/Vector 核做流水）来取性能时。控核有固有代价——每条流只能用部分核、算子受算力约束。

## 问题信号（控核的代价，实测）

同卡多流为并行给两条流分核后，各计算算子因只能用部分核而变慢。同配置、仅核数不同、从整网采集拆解：

| Cube_Vector 核数 | MLA_Prolog(us) | FA(us) | MM(us) | TBMM(us) | QBMM1(us) | QBMM2(us) |
|---|---|---|---|---|---|---|
| 12C_24V（控核） | 68.1 | 118 | 18 | 19.6 | 18.7 | 20.1 |
| 24C_48V（不控核） | 45.2 | 91.8 | 14.2 | 12.5 | 14.6 | 16.3 |

即不控核时算子耗时显著下降——控核是同卡多流方案的固有代价。

## 做什么（AFD）

把 MoE/FFN 模块从整网剥离、与 Attention 分处不同 rank，两侧用点对点 Send/Recv 交互：

- **拓扑**：Attention 侧纯 DP + 投影层局部 TP（`attn_tp_size:1` / `o_proj_tp_size:8` / `dense_tp_size:8`）；FFN 侧纯 EP（`moe_tp_size:1`，`moe_ep_size = ffn_world_size`）。
- **计算流水**：Attention 节点第一个 LayerNorm 结果一路 Send 给 FFN 节点、一路继续本地计算；Send 后 Recv 等 FFN 回传。Attention 侧 Send/Recv 放 Stream1、与主流 Stream0 计算 overlap 达通信-计算隐藏。FFN 节点首算子是 Recv（阻塞等 Attention 发来），收到后做 Router/Dispatch/MoE-GMM/Combine 再 Send 回。
- **关键：Send/Recv 跨节点走 SDMA、不占用 Vector 核**，所以 Attention 侧计算算子与 Send/Recv 并行时**不再受控核约束、可用满核** → 各算子耗时回落到「不控核」水平 → 降 decode TPOT。

## 前置 / rank 划分（Send/Recv 的硬约束）

- Send/Recv 单次通信当前只支持 **1:1**（不支持 M:N），故 Attention Instance 节点数必须等于 FFN Instance 节点数（**M==N**）。规划节点前先按此定总数。
- `world_size` 必须为**偶数**（`update_afd_settings` 对奇数抛 `ValueError`）；`ffn_world_size = world_size // 2`；`global_rank < ffn_world_size` 判为 FFN rank、否则 Attention rank（前半 FFN / 后半 Attention）。
- 收发配对：Attn rank R 与 FFN rank `R ± ffn_world_size` 同层同向配对；tag 用 `send_tag=layer_idx` / `recv_tag=layer_idx+num_hidden_layers`（Attn 的 send tag == FFN 的 recv tag，避免收发 tag 重叠）。
- FFN rank 只跑 MoE（Router/Dispatch/GMM/Combine），无 Attention、无 MTP；AFD 下 Attention 侧 `moe_tp_group/moe_ep_group` 置 None。

## 何时不适用 / 常见坑 / rollback

- **多流控核旋钮与 AFD 互斥**：`enable_multi_stream` 在 AFD 场景不生效（走 Send/Recv over SDMA 隐藏通信、非多流控核路径）。开 AFD 就别再指望多流控核旋钮。
- **别默认为解耦加全局 barrier**：初期为规避两侧权重加载时间差导致通信超时而加的 `dist.barrier`，review 中删除、作者确认删后仍正常——解耦部署的通信超时不必用全局 barrier 兜底。
- **perfect_eplb 影响精度**：测 TPOT 常配 `perfect_eplb: True`，仅供 TPOT 测试、会拉低精度，落地精度评估须关闭（见 [perfect-eplb-profiling-upper-bound](../rules/perfect_eplb_profiling_upper_bound.md)）。
- **参考实现约束非技术约束**：Send/Recv 1:1 → M==N 是当前实现约束（M:N 为后续计划），迁移 AFD 思想到别的 MoE 不受此限，照搬这套 Send/Recv 代码才受限。
- rollback：关 AFD 开关即回同卡多流控核路径，`ffn_world_size` 归 0、全部 rank 作 Attention rank。
- 关联：AFD 后 FFN 侧易成新瓶颈，见 [afd-ffn-side-bottleneck-prefetch](../../../runbooks/performance/afd_ffn_side_bottleneck_prefetch.md)。

## Benchmark（仓自报，无独立复测）

Atlas A3、LongCat-Flash W8A8、MTP2 + perfect eplb：

| Enable AFD | Global Batch | Seq | Chips | TPOT(ms) | Throughput(tokens/p/s) |
|---|---|---|---|---|---|
| N | 512 | 4608 | 64 | 10.37 | 771.46 |
| N | 256 | 4608 | 32 | 10.64 | 751.88 |
| N | 256 | 4608 | 64 | 9.95 | 402.01 |
| Y | 256 | 4608 | 64 | 9.5 | 421.05 |

**唯一同配置受控对比**（64 chips / GBS 256 / seq 4608）：AFD 使 TPOT 9.95→9.5 ms、吞吐 402.01→421.05，进入 10ms 内且优于不分离。其余行 chips/GBS 不同、非受控对比；不外推单调规律。软件 CANN 8.5.0（SuperKernel 标记范围内部分算子当前尚不支持完全融合）。

## Evidence

- AFD send/recv 接线、`enable_afd` 分支、`limit_core_num(not self.enable_afd, ...)`、rank 划分、新增 FFN 侧 `recv→router→moe→send`：diff 事实 @72495f0ee845；控核耗时表与 TPOT 数字为 doc 披露（仓自报、无独立复测）。溯源下探 [cann-recipes-infer-pr-249-feat-longcat-support-attention-ffn-disaggregation-afd](https://gitcode.com/cann/cann-recipes-infer/merge_requests/249)、[cann-recipes-infer-issue-99-rfc-longcat-flash-model-support-afd-feature](https://gitcode.com/cann/cann-recipes-infer/issues/99)。
- `world_size%2==0` 校验 + `ffn_world_size=world_size//2` + 前半 FFN/后半 Attn：diff 事实 @72495f0ee845；Send/Recv 1:1、M==N 为 doc 披露且与代码自洽；barrier 删除为维护者/作者确认。