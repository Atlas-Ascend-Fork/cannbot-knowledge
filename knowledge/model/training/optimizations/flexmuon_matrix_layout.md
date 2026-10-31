---
type: Optimization
title: FlexMuon：按完整逻辑矩阵重组分片并重叠状态搬运
description: 在 950 分布式 Muon 中，以矩阵完整性决定重组通信，结合 NovaSwap 与 owner replica，保持优化器数学语义和状态归属。
tags:
- task.optimization
- topic.optimizer
- topic.parallelism
- topic.memory
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/ascend950/flexmuon.md
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/muon_optimizer.md
  role: supporting
created_at: '2026-10-29T04:09:06Z'
updated_at: '2026-10-29T15:39:15Z'
platforms:
- '950'
---

# FlexMuon：按完整逻辑矩阵重组分片并重叠状态搬运

## 场景、信号与规则

FSDP 将参数长期分片，而 Muon 的 Newton–Schulz 要作用于完整逻辑矩阵。先判断本地 shard 是否包含完整 Expert、head 或 group 矩阵，只有矩阵被切开时才通信重组，不能对任意局部分片直接正交化。

## 机制与实施

普通 Dense 参数用第一次 AllToAllV 将有效梯度重组成各 owner 负责的完整矩阵，完成 Newton–Schulz 后用第二次 AllToAllV 返回原 FSDP 分片，再由参数所属 rank 更新。本地已有完整矩阵时可批量计算，省去布局转换通信。

NovaSwap 独立管理优化器状态驻留：使用前异步 H2D，生成有效梯度后状态不再被后续矩阵计算读取，可 D2H 回写；复制结束才释放设备空间。锁页 CPU 内存池减少反复分配。相邻层和两套 buffer 提供搬运、重组与计算的重叠窗口，复用前须等待上一次返回和参数更新。

HSDP replica 去冗余为每个参数选择 owner，仅 owner 保存状态、执行优化器流程，再把更新后的参数分片广播给副本。checkpoint 时恢复标准状态布局，续训后重建 owner 关系。

## 收益、代价与回退

收益来自减少重复状态、矩阵计算、中间数据与未掩盖通信；代价包括 Host 锁页内存、布局转换、buffer 和调度同步。源文档中的通信下降、算子计算下降与 HSDP 耗时下降针对不同局部指标，不能相乘或相加为整网收益。

关闭 Swap 后仍应沿原 Muon 更新语义运行。重叠或 owner 路径不能通过正确性验证时回到已验证的同步/标准状态路径，重新评估显存容量。

## 验证与版本边界

在相同梯度下对比完整逻辑矩阵的更新方向、各分片参数与动量，检查 buffer 生命周期、replica 一致性及 checkpoint 续训。当前DistMuon/FlexShard 文档只验证 TP=1、PP=1；state swap 是显式 override，不能与 Virtual Optimizer 同时启用。HSDP replica dedup 默认关闭。swap checkpoint 支持同步与 async，尚未证明 async_with_pinned_mem 或跨 world size 恢复。该实现已不同于旧 torchtitan-npu 单设备 Muon；历史接口和限制见 [Muon 优化器](../concepts/techniques/muon_optimizer.md)。本批仅蒸馏固定技术文档，未执行训练。
