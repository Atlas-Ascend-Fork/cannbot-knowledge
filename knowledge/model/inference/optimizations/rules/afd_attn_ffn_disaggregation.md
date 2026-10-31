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
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/ffn.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:24:40Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
      model_features:
        all_of:
        - moe
      deployment_topology:
        all_of:
        - afd
---

# Attention-FFN 解耦（AFD）部署：把 MoE/FFN 剥到独立 rank，Send/Recv over SDMA 解除同卡多流控核约束降 decode TPOT

## 适用场景

大规模 MoE 在图模式 decode 阶段遇到 host-bound / TPOT 瓶颈，且现方案是 Attention 与 MoE 同卡、靠多流并行「控核」（`limit_core_num` 给 Attention 流与 MoE 流分配部分 Cube/Vector 核做流水）来取性能时。控核有固有代价——每条流只能用部分核、算子受算力约束。

## 问题信号

同卡多流为不同计算路径分配部分 Cube/Vector 核，可能增加各算子的计算耗时。固定来源的核数对比与整网数据集中在[LongCat A3 来源观测](../benchmark_observations/longcat_a3_afd_source_benchmark.md)，不以这些数字推导任意模型的收益。

## 做什么（AFD）

把 MoE/FFN 模块从整网剥离、与 Attention 分处不同 rank，两侧用点对点 Send/Recv 交互：

- **拓扑**：Attention 侧纯 DP + 投影层局部 TP（`attn_tp_size:1` / `o_proj_tp_size:8` / `dense_tp_size:8`）；FFN 侧纯 EP（`moe_tp_size:1`，`moe_ep_size = ffn_world_size`）。
- **计算流水**：Attention 节点第一个 LayerNorm 结果一路 Send 给 FFN 节点、一路继续本地计算；Send 后 Recv 等 FFN 回传。npugraph_ex Decode 将接收延迟到本地计算结束、相加前；设备侧实际重叠需查看时间线。FFN 节点首算子是 Recv（阻塞等 Attention 发来），收到后做 Router/Dispatch/MoE-GMM/Combine 再 Send 回。
- **关键：Send/Recv 跨节点走 SDMA、不占用 Vector 核**，所以 Attention 侧计算算子与 Send/Recv 并行时**不再受控核约束、可用满核** → 各算子耗时回落到「不控核」水平 → 降 decode TPOT。

## 前置 / rank 划分（Send/Recv 的硬约束）

- Send/Recv 单次通信当前只支持 **1:1**（不支持 M:N），故 Attention Instance 节点数必须等于 FFN Instance 节点数（**M==N**）。规划节点前先按此定总数。
- `world_size` 必须为**偶数**（模型和通信组初始化对奇数抛 `ValueError`）；`ffn_world_size = world_size // 2`；`global_rank < ffn_world_size` 判为 FFN rank、否则 Attention rank（前半 FFN / 后半 Attention）。
- 收发配对：Attn rank R 与 FFN rank `R ± ffn_world_size` 同层同向配对；tag 用 `send_tag=layer_idx` / `recv_tag=layer_idx+num_hidden_layers`（Attn 的 send tag == FFN 的 recv tag，避免收发 tag 重叠）。
- FFN rank 只跑 MoE（Router/Dispatch/GMM/Combine），无 Attention、无 MTP；当前 CommManager 在两半分别注册业务通信组，不再沿用旧 hccl_comm_dict 置 None 的描述。

## 何时不适用 / 常见坑 / rollback

- **AFD 关闭本地 MoE 分流控核，仍使用多流入口**：`forward` 在 `model_config.custom_params.enable_multi_streams > 0` 且非 Prefill 时进入 `multi_stream_forward`，不排除 AFD；AFD 分支用 `limit_core_num(not self.enable_afd, ...)` 关闭本地控核。当前模型直接拒绝预取开启而多流关闭的组合，不能把配置注释解释为该开关无效或与 AFD 互斥。
- **别默认为解耦加全局 barrier**：初期为规避两侧权重加载时间差导致通信超时而加的 `dist.barrier`，review 中删除、作者确认删后仍正常——解耦部署的通信超时不必用全局 barrier 兜底。
- **perfect_eplb 影响精度**：测 TPOT 常配 `perfect_eplb: True`，仅供 TPOT 测试、会拉低精度，落地精度评估须关闭（见 [perfect-eplb-profiling-upper-bound](perfect_eplb_profiling_upper_bound.md)）。
- **参考实现约束非技术约束**：Send/Recv 1:1 → M==N 是当前实现约束（M:N 为后续计划），迁移 AFD 思想到别的 MoE 不受此限，照搬这套 Send/Recv 代码才受限。
- rollback：关 AFD 开关即回同卡多流控核路径，按关闭后的完整非 AFD 配置重新初始化 rank/通信组，不能在既有运行态原地复用。
- 关联：AFD 后 FFN 侧易成新瓶颈，见 [afd-ffn-side-bottleneck-prefetch](../../runbooks/performance/afd_ffn_side_bottleneck_prefetch.md)。

## 来源观测与验证

完整 workload、核数耗时和 TPOT/吞吐集中在[LongCat A3 来源观测](../benchmark_observations/longcat_a3_afd_source_benchmark.md)。来源的 MTP2 与 perfect EPLB 条件不等于真实路由已通过精度验收；迁移时保存实际配置、输出、计时和重复记录，再判断 AFD 是否获益。本次未执行模型或验证回退。

## Evidence

- [longcat_flash_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md)（primary）
- [modeling_longcat_flash.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py)（implementation）
- [ffn.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/ffn.py)（implementation）
