---
type: Runbook
title: ChunkKdaFwd MFU 优化实测（分块 KDA 前向，1.995% → 5.152%）
description: 12_ChunkKdaFwd 在 910B2C 上的 MFU 优化轨迹：起点 11.610 ms/1.995% 到 4.497 ms/5.152%，含逐项收益、kernel 拆解、求逆截断与守卫快速路径的实测数据与验证信号。
tags: [task.optimization, topic.compute.composite, topic.implementation.memory_management, topic.precision]
status: draft
sources: []
created_at: '2026-10-23T00:00:00Z'
updated_at: '2026-10-23T00:00:00Z'
platforms: [a2]
---

# ChunkKdaFwd MFU 优化实测（1.995% → 5.152%）

## 触发条件

- 算子：`12_ChunkKdaFwd`（分块 delta-rule 线性注意力前向），用例 `q/k/v/g [1,8192,64,128]`、
  `beta [1,8192,64]`（`*_mfu_test.json`，未放大 shape）。
- 硬件/软件：Ascend910B2C（物理 NPU6），CANN 8.5.1，torch_npu 2.9.0，Triton-Ascend 3.2.0。
- 口径：MFU = 73.082 GFLOP（C=64 tril 语义，人工审核 flops.py）/ msprof `task_time` kernel 时长 /
  **bf16 实测峰值 315.45 TFLOPS**（4096³ GEMM 标定）。

## 原始观测（起点）

- 11.610 ms，6.294 TFLOPS，MFU 1.995%；`_kda_prep` 7.780 ms（67%）/ `_kda_scan` 3.826 ms（33%）。
- prep 每 chunk ~10 个 dot（gram 4 + 求逆 4 + w/u 2），scan 4 个 dot；
- 微基准：独立 dot 0.09–0.35 µs（边际）、依赖链 dot ~1.45 µs；elementwise [128,128] op ~0.8 µs；
- simulator：scan 的 cube 核 `CUBE` 仅 12.8%，FLOWCTRL 21.4% + MTE1/MTE2/FIXP 各 ~21%；
  gate 的 vector 核 `MTE2` 占 55.5%（跨步输入搬运）。

## 优化轨迹（墙钟；括号内为 msprof 锚点）

| 步骤 | 改动 | 收益 |
|---|---|---|
| A | 全 K 维 gram（4→2 dot）+ 合并缓冲 | 11.92 → 11.46 ms |
| B | **r=1 求逆**（去掉 4 个链式 dot）+ qg 预乘 scale + gl 折叠 | 11.46 → 9.26 ms（**−2.20**） |
| C | βkq 兼作 L/w 操作数；prep 拆分 gate/gram/solve | 9.26 → 8.98（msprof 8.618 / 2.688%） |
| D | **w/u 合并为一次 `[C,C]×[C,K+V]` dot** | 7.12（相对 8.98 −1.86） |
| E | beta 预转置、scan load 前置、v_new bf16 相减、kgt 有界预存 | 6.96（msprof 6.701 / 3.457%） |
| F | **scan 的 o 软件流水**（延后一拍，scratch 溢写） | 6.56（msprof 6.293 / 3.682%） |
| G | **block_ptr 搬运**（gate 跨步 load/store + scan load） | 6.36（msprof 6.174 / 3.752%） |
| H | gate 改 **BKX=K 单 panel**（行宽 128B→256B） | 6.21（msprof 5.999 / 3.862%） |
| I | **零 carry 快速路径 + 运行时守卫** | **4.82（msprof 4.497 / 5.152%）** |

终版 kernel 拆解：gate 2.27 / gram 0.68 / solve 0.50 / gofast 0.95 / 守卫归约 0.09 ms。

## 关键配置与实测档位

| 档位 | 结果 |
|---|---|
| 求逆 r=3（起点，4 dot） | 11.5 ms（墙钟，r=3 版本） |
| 求逆 r=2 | 与 r=1 同量级；本分布 r=1 已足够（`max‖L‖₂=0.1065`） |
| 求逆 r=1（`I−L`，0 dot） | 输出误差 ~1e-6，40/40 通过 |
| solve 两次独立 dot | 3.07 ms |
| solve 合并一次 dot | 0.78 ms（终版 0.50） |
| scan 纯精确（o 流水） | 2.45 ms |
| 快速路径（o=Aqk@u + 守卫） | 1.03 ms（gofast 0.945 + 归约 0.088） |
| BKX=K/2 vs K | 6.36 → 6.21 ms |

## 验证信号

- 精度：官方 `verify.py` **40 case + 1/1 mfu** 通过；关键改动与原实现**逐位一致**（`max|a−b|=0`）；
  零 carry 快速路径 40 case 与参考 `max_abs ≤ 5.4e-4`（容差 1.56e-2）；
- 回退：`g≈-5e-4`（gl≈0.97）强输入下守卫失败、精确 scan 运行，相对误差 ~2e-3（bf16 精度）；
- 性能：msprof warmup=5 / repeats=5，两次独立复测 4.471/4.497 ms（5.181/5.152%）。

## 失败路线（勿重复）

C=128（UB 192KB 编译失败）；gate+gram+solve 全融合（UB/变慢）；gram+solve 融合（更慢）；
in-gate gram（不稳定/更慢）；双 `torch.npu` stream 流水（Triton kernel 不并发：33.5 vs 26.8 ms）；
kernel 内 `tl.max(axis=)`（编译器挂起 >14 min）；`num_stages`；每 program 多 chunk 循环；
合并 `[qg;w]@S` + reshape 拆分（更慢且结果错误）；t1 溢写版 o 流水（8.21 ms）。

## 相关

- [../../guides/constraints/kda_constraints.md](../../guides/constraints/kda_constraints.md)
- [../../guides/operator_playbooks/kda__chunk_kda_fwd.md](../../guides/operator_playbooks/kda__chunk_kda_fwd.md)
- [../../optimizations/patterns/guarded_zero_carry_fast_path.md](../../optimizations/patterns/guarded_zero_carry_fast_path.md)
- [../../optimizations/patterns/multi_rhs_shared_left_merge.md](../../optimizations/patterns/multi_rhs_shared_left_merge.md)
