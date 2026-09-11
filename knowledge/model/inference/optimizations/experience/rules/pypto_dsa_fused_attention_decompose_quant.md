---
type: Optimization
title: 在昇腾用 PyPTO 落地 DSA/复杂融合注意力：分阶段拆-融合组织 + 低 bit 量化融合算子关键手段
description: 在昇腾用 PyPTO 落地 DSA/复杂融合注意力：分阶段拆-融合组织 + 低 bit 量化融合算子关键手段。要在昇腾上把一个复杂的稀疏/融合注意力（如 DSA indexer attention）做成高性能融合算子，用 PyPTO（MPMD 调度、类 Mega Kernel、开发者自选融合范围 + Human-In-The-Loop 泳道图调优）落地：既要「怎么组织开发（拆多大、融多大）」，也要「低 bit 量化融合算子怎么压到带宽极限」。
tags:
- task.optimization
- topic.attention
- topic.precision
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/12
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 在昇腾用 PyPTO 落地 DSA/复杂融合注意力：分阶段拆-融合组织 + 低 bit 量化融合算子关键手段

## 适用场景
- 要在昇腾上把一个复杂的稀疏/融合注意力（如 [DSA](../../../concepts/modules/dsa.md) indexer attention）做成高性能融合算子，用 [PyPTO](../../../concepts/frameworks/pypto.md)（MPMD 调度、类 Mega Kernel、开发者自选融合范围 + Human-In-The-Loop 泳道图调优）落地：既要「怎么组织开发（拆多大、融多大）」，也要「低 bit 量化融合算子怎么压到带宽极限」。

## 组织方法：分阶段拆-融合
- **先拆再逐步扩融合**：先手动写各相对独立的子算子、各自调优，再由框架逐步把它们融合成更大的算子——「在更大的范围内融合有更大的并行度可以挖掘」。DSA 大算子（[Deepseek Indexer Attention](../../../concepts/kernels/deepseek_indexer_attention.md)）逻辑上由 [MLA Prolog](../../../concepts/kernels/mla_prolog.md)、[Indexer Prolog](../../../concepts/kernels/indexer_prolog.md)、[Lightning Indexer](../../../concepts/kernels/lightning_indexer.md)、[Sparse Flash Attention](../../../concepts/kernels/sparse_flash_attention.md) 四个相对独立部分构成。
- **融合粒度是取舍量、随迭代演进**：初期交付 3 个融合算子（MLA_IP_Prolog=MLA+Indexer Prolog / LI / SFA），主干后续细化为 5 个（mla prolog / mla_indexer_prolog / lightning indexer prolog / lightning indexer / sparse flash attention）。规划融合边界时按当前交付粒度、不认死固定数。

## 低 bit 量化融合算子关键手段（Indexer Prolog 为例）
写 attention 前段（Indexer Prolog，即 Deepseek Indexer Attention 前半）的低 bit 量化融合算子时，把 MTE-bound 的算子推向带宽极限的手段：
- **量化前做 Hadamard 消 outlier**：低 bit（A8/C8）量化 Q/K 时 outlier 放大量化误差 → 量化前右乘 Hadamard 矩阵（Q 侧右乘 hadamard_q、Cache 侧右乘 hadamard_k）压 outlier，这是通用手段。
- **量化布局**：Indexer Q 用动态 per-token-head A8、Indexer Cache 用 C8（见 [w8a8c8](../../../concepts/quantization/w8a8c8.md)），反量化 scale 以 FP16 存；权重侧仅 Q_b_proj 走 W8A8、其余 Linear 不量化；Indexer Weight 分支不量化、末端转 FP16 供后续 [Lightning Indexer](../../../concepts/kernels/lightning_indexer.md) 使用。
- **撑大 Matmul M 轴**：`b*s1` 合轴撑大 M 轴，让 MTE-bound 的 Matmul 计算更充分；多路 Matmul（q / k / weight）并行抢带宽掩盖 MTE 时延。
- **数据留 UB、避免冗余搬运**：DeQuant + RoPE + 动态量化全部留在 Vector 核 UB 上算，不产生 UB↔GM 冗余往返。

## 边界
- 长 KV-Cache decode 下该类算子由 Indexer Q 的 MTE 搬运决定上限；上述手段可把 kernel 推到逼近 MTE 带宽理论极限（仓自报、无独立复测，仅报告的典型 shape 成立，不外推单调律）。
- 子算子数与命名随版本漂移（3→5），按当前交付粒度规划、不认死固定数。
- 注意兼容性：C8 KVCache 量化与 PyPTO 版 Lightning Indexer 加速当前互斥、不能叠加，见 [c8-kvcache-disables-pypto-lightning-indexer](../anti_patterns/c8_kvcache_disables_pypto_lightning_indexer.md)；压 Lightning Indexer 单算子时延的量化算子选型见 [quant-lightning-indexer-latency](quant_lightning_indexer_latency.md)。

## 参考实现及其约束
- 参考 [deepseek-v3.2-exp](../../../concepts/models/deepseek_v3_2_exp.md) 的 DSA indexer attention（典型 4 Batch、MTP1、KV 64K，decode / 长 KV-Cache），量化系数/布局/融合粒度为该参考实现细节。

## Evidence
- `维护者确认` + `diff 事实`（@87f244c；pypto@c45d961）：维护者明确四部分构成 + 3 算子拆解（MLA_IP_Prolog/LI/SFA）；pypto `models/deepseek_v32_exp/README.md` 首段列 5 个交付算子，与 docs guide 合并文本一致（算子数 3→5 随版本漂移）。Hadamard + A8/C8 量化方案与新增 kernel `quant_lightning_indexer_prolog.cpp`、`lightning_indexer_prolog_pto/` 目录见同 sha。
- `仓自报`：「逼近理论极限」为仓自报、无独立复测；tiling/bubble/vector 与性能数字据实分层、不并入事实面。
- 溯源下探：[cann-recipes-infer-issue-12-rfc-pypto](https://gitcode.com/cann/cann-recipes-infer/issues/12)