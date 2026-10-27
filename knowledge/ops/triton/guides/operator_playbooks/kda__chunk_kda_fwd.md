---
type: Guide
title: ChunkKdaFwd 算子（分块 KDA 前向）实现手册
description: '典型特征: q/k/v/g [B,T,H,K] + beta [B,T,H]，C=64 分块，块内 Aqk/L 两个 gram + (I+L)⁻¹ + w/u 求解，块间 [K,V] 状态 scan；实测 MFU 1.995% -> 5.152%'
tags: [task.implementation, topic.compute.composite, topic.precision, topic.implementation.memory_management, topic.tiling]
status: draft
sources: []
created_at: '2026-10-23T00:00:00Z'
updated_at: '2026-10-23T00:00:00Z'
platforms: [a2]
---

# ChunkKdaFwd 算子（分块 KDA 前向）实现手册

> 类别约束见 [../constraints/kda_constraints.md](../constraints/kda_constraints.md)（L1.1~L1.9），
> 全局约束见 [../constraints/global_constraints.md](../constraints/global_constraints.md)。

**算子类别**: `kda`（chunked delta-rule 线性注意力）
**典型特征**: `q/k/v/g [B,T,H,K]`（bf16/fp32）、`beta [B,T,H]`；C=64 分块；块内两个 gram + 三角求逆 + 两个右端求解；块间 `[K,V]` 状态递推。
**性能基准**（`12_ChunkKdaFwd`，mfu_test `[1,8192,64,128]`，910B2C/NPU6，CANN 8.5.1，Triton-Ascend 3.2.0）：
起点 **11.610 ms / MFU 1.995%** → 终版 **4.497 ms / MFU 5.152%**（2.58×）；精度官方 `verify.py`
**40 case + mfu case 双通过**（终版复跑多次）；MFU 分母为 bf16 实测峰值 315.45 TFLOPS。
全部消融与产物见 `性能优化/12_优化过程/`（report.md / summary.json / dev/）。

## Layer 2 算法骨架（C=64，三 kernel + 可选快速路径）

```text
# K1 beta 预转置  grid=(B*M,)   [B,T,H] -> [B,H,Tp]，后续 kernel 连续取列
# K2 gate        grid=(B*H*M,) 0 dot
gk = cumsum(g)/ln2 ; e = exp2(gk) ; ei = exp2(-gk) ; gl = exp2(sum(g)/ln2)
qg  = (q*e*scale).bf16        # scale 预乘，scan 侧不再乘
kq  = (k*e*β).bf16            # βkq：L 与 w 的公共右端
kgq = (k*ei).bf16 ; kqt = trans(kgq)
kgt = (kqt*gl).bf16           # 有界（≤|k|），scan 用；不要存未缩放 kqt 给 scan
store qg, kq, βv（与 βkq 拼成连续 [C,K+V]）, kqt, kgt, gl(fp32)
# K3 gram        grid=(B*H*M,) 2 个独立 dot
Aqk = tril(dot(qg, kqt)) ; L = tril(dot(kq, kqt), -1) ; rb = (I − L).bf16
# K4 solve       grid=(B*H*M,) 1 个 merged dot
res = dot(rb, [βkq | βv])     # [w | u]
# K5 状态 scan   grid=(B*H,)：精确路径（块间串行）
v_new = u − w@S ; o = qg@S + Aqk@v_new ; S = gl⊙S + kgt@v_new
# 可选：零 carry 快速路径（守卫通过时） o = Aqk@u，见 pattern 卡
```

## 关键实现要点（实现优先序）

按"先消除链式/冗余 dot，再优化搬运与流水"的顺序落地；各项的实测收益、配置档位与对照数据见
[../../runbooks/performance/chunk_kda_fwd_mfu.md](../../runbooks/performance/chunk_kda_fwd_mfu.md)。

1. **求逆 r=1**：`rb = I − L`（先按约束卡 L1.2 测 `max‖L‖₂` 再定 r）。
2. **merged solve**：`[w|u] = (I−L) @ [βkq|βv]`，一次 `[C,C]×[C,K+V]` dot（见 pattern `multi_rhs_shared_left_merge`）。
3. **零 carry 快速路径 + 守卫**：`o=Aqk@u`，守卫与回退见 pattern `guarded_zero_carry_fast_path`。
4. **block_ptr + BKX=K**：gate 的跨步 load/store 全 block_ptr；单 panel 行宽 128B→256B。
5. **o 软件流水**（精确路径适用）：o 延后一拍，用上一轮 `v_new/S_bf16`（scratch 溢写；编译器不支持寄存器携带）。
6. β 预转置、scan 的 6 个 load 前置、v_new 在 bf16 域相减。

## 精度与验证

- 数值安全规则见约束卡 [L1.5/L1.8](../constraints/kda_constraints.md)：`ei = exp2(-gk)`、有界 kgt。
- 本算子校验集：官方 `verify.py` 原 40 case + mfu case（mfu 单 case 输出仅 ~1e-4，**不能单独作为判据**，
  必须先过 40 case 并与精确实现逐位对拍）。
- 快速路径回退验证：`g≈-5e-4`（慢衰减）下守卫失败、精确 scan 运行，相对误差 ~2e-3（bf16 精度）。

## 已实测否决

失败路线与原因见 runbook 的「失败路线」一节；实现时不要重复尝试。

## 相关

- [../constraints/kda_constraints.md](../constraints/kda_constraints.md)
- [../../optimizations/patterns/guarded_zero_carry_fast_path.md](../../optimizations/patterns/guarded_zero_carry_fast_path.md)
- [../../optimizations/patterns/multi_rhs_shared_left_merge.md](../../optimizations/patterns/multi_rhs_shared_left_merge.md)
- [../../runbooks/performance/chunk_kda_fwd_mfu.md](../../runbooks/performance/chunk_kda_fwd_mfu.md)
