---
type: Runbook
title: BlockSparseAttentionGrad 算子（block-sparse-attention-bwd） 实现手册
description: BlockSparseAttentionGrad（BNSD/MHA/D=128、bx/by 16~128 可非对称、17 case）实测：kv 主序表若用 strided 列 gather 建表会 ub overflow（401KB，带循环或无循环 P2=128 均复现），改用 device 侧 uint8 掩码转置 kernel + 连续行 load 后一次编过；dk/dv kernel 必须独立选 tile（BMK=min(bx,64)；BT 取整除 by 的最大值：by≤32 取 by，否则依次试 32/48/16）否则 224KB 越界；17/17 精度通过，基线 geomean 0.034x（Phase 3 未优化）。
tags: [task.optimization, topic.attention, topic.implementation.masking, topic.tiling, topic.memory, topic.precision]
status: draft
sources: []
created_at: '2026-10-21T00:00:00Z'
updated_at: '2026-10-22T00:00:00Z'
verified:
- by: process:opencode-deepseek-flash-tt36
  at: '2026-10-21T00:00:00Z'
platforms: [a2]
---

# BlockSparseAttentionGrad 算子（block-sparse-attention-bwd） 实现手册

> 类别约束见 [block_sparse_attention_constraints.md](../../guides/constraints/block_sparse_attention_constraints.md)，
> 全局约束见 [global_constraints.md](../../guides/constraints/global_constraints.md)。

## 任务特征

- 形态：三·2 块跳过 + `sp-bwd`（入参 dO/O/LSE，出 dQ/dK/dV），MHA（无 GQA），BNSD、D=128。
- 掩码：`blockMask[B,N,ceil(S/bx),ceil(S/by)] uint8`，bx/by ∈ {16,32,48,64,80,128}（可非对称），golden 用 token 级 `where(mask)` 表达。
- 17 case：S=1024~8192，fp16×16 + bf16×1，pattern causal/window/bigbird/random/dense，含 S=2000/4032 非整除边界。

## 骨架（5+1 kernel，全部 device 侧建表，host 只做 shape/alloc/view）

```
mask_transpose -> sel_q(q 主序) / sel_k(kv 主序) -> delta -> dq -> dkdv
```

- `sel_q[B,N,NRQ,NKB]`：行 = q tile（BM 行），列域 = kv 子块（BN 行）。
- `sel_k[B,N,NRK,NQB]`：行 = kv 子块（BT 行），列域 = q tile（BMK 行）。
- 两表都用**比较矩阵前缀计数**紧致化（`pos = sum(where(loc[:,None] > loc[None,:], keep, 0), 1)`），禁 `tl.cumsum`；计数值换算 fp16 可再省一半 UB。

## 坑 1（头号，必踩）：kv 主序表不要用 strided 列 gather

```python
# ❌ ub overflow 401KB（requires 3211264 bits while 1572864 available）
keep = tl.load(bmask_ptr + (bnidx * NQBLK + qts) * NKBLK + kb, mask=qts < NQB, other=0)
# 触发条件实测：gather 长度 >= 128；或 gather + 任意外层循环（即便 NCH=1）
```

最小复现结论：同样的紧致化流程，**q 主序的连续 load 在 P2=128/带 4 段 chunk 循环下都能编过**，只有「strided gather + 循环」或「strided gather 长度 128」爆 UB。

```python
# ✅ 先做一个 device 侧 uint8 掩码转置 kernel（纯布局，无 dot/atomic，tile = next_pow2(max(nqb,nkb))）
v = tl.load(bmask_ptr + base + j[None, :] * NKBLK + i[:, None], mask=mk, other=0)   # [nkb, nqb]
tl.store(bmt_ptr + pid * NKBLK * NQBLK + i[:, None] * NQBLK + j[None, :], v, mask=mk)
# 之后 sel_k 只读连续行：tl.load(bmt_ptr + rbase + mqs, mask=qts < NQB)
```

转置 kernel 的 stried 访问是**一次**完成且 tile 很小（uint8，≤16KB），与「每个 (b,kt) 行都 gather 一遍」量级不同——实测转置结果与 `mask.permute(0,1,3,2)` 逐位相等。

## 坑 2：kv 主序表的列粒度映射

`sel_k` 的列是 **q tile（BMK 粒度）**，而转置掩码的列是**掩码块（bx 粒度）**。`bx > BMK` 时必须映射，否则索引越界且 dk/dv 全错（首版 maxabs=2.8、meanrel=12）：

```python
mqs = qts // (bx // BMK)      # q tile -> mask block column，再 tl.load(bmt + rbase + mqs)
```

## 坑 3：dk/dv kernel 的 tile 必须独立于 dq

同一个 `BM=BN=64`、`BT=64`、D=128 在 dkdv 上需要 224KB（两个 `[BT,D]` fp32 累加器 + 4 个 `[BT,BM]` fp32 中间量 + q/dout 各两份）→ ub overflow。实测可编梯度：

| kernel | 配置 | 结果 |
|---|---|---|
| dq | BM=64, BN=64 / BN=80 | 可编 |
| dkdv | BMK=64, BT=32 | 可编（最大 case S=8192 亦通过） |
| dkdv | BMK=BM=64, BT=64 | ub overflow |

规则：`BMK = min(bx, 64)`（整除 bx）、`BT = by if by<=32 else 32 if by%32==0 else (48 if by%48==0 else 16)`（整除 by，保证 kv 子块唯一归属一个掩码块）。

## 精度配方（fp32 参考、fp16/bf16 输出，eco 口径 17/17 通过）

- `q/k/v/dout` 原生 dtype 进 `tl.dot`，fp32 累加器（禁升 fp32  operand）。
- `p = exp(s - lse)` 与 `ds = p*(dp - delta)` 是真 fp32 量：喂 dot 前 **hi+lo 二段拆分**（`ph = p.to(DTYPE); pl = (p - ph.to(f32)).to(DTYPE)`），dq/dk/dv 三路都做。
- 边界列 `tl.where(valid, s, -3e38)`（constexpr），越界行地址先 `min(idx, S-1)` 再 mask。
- 输出 lse/delta 全为**输入给定/fp32**，反向无除法，故无 NaN 风险；`cnt==0` 行自然得 0。

## 实测（Ascend 910B3 20 AIC / 40 AIV，triton_ascend 3.6.0（tt36）+ CANN 9.1.0 + torch 2.10.0 / torch_npu 2.10.0.post7）

| 项 | 值 |
|---|---|
| 精度 | 17/17（eco：fp16 atol=rtol=2^-9，bf16 2^-6，matched_ratio≥0.99） |
| 基线 geomean（Phase 3，未优化） | **0.0340x**（impl 几何均值 185.87ms / fw 6.31ms） |
| kernel 热点 | `_dkdv_kernel` 181.6ms、`_dq_kernel` 146.9ms |
| 最差 case | bx48/by80 causal（0.0059）、dense S2048（0.0149） |

> 该基线是「正确性优先」形态（数据依赖 `range(cnt)` 循环、hi+lo 双份 dot、dkdv 里 q/dout 各 load 两次、无流水/多缓冲）。

## 最终优化结果（同环境，6 轮有效 + round2 追加 2 轮）

| 项 | 值 |
|---|---|
| 全 17 case triton 总核时 | 5934.7 ms → **21.67 ms（273.8x）** |
| 对 AscendC 标杆（aclnnBlockSparseAttentionGrad，ops-transformer） | geomean **0.9283**，min 0.6815，**17/17 > 0.6** |
| 反超标杆 case | 4 个（最高 3.41x） |

## 后续优化方向（实测结论）

原三个方向的验证/否决结果：

- ① 取消 q/dout 二次 load —— **已验证**：单遍 5-dot 融合（dq/dkdv 合并为每 pair 1 次迭代）+ dk/dv partial workspace + reduce，geomean 0.47 → 0.672 档。
- ② 重扫 `BN/BT` —— **已验证**：`tl.dot(a,b,acc)` 3 参把累加器放上 cube，dq tile 上界 128×128、dk/dv BMK=128；`BT=128`（dk/dv 输出行）不可用——两个 [128,128] fp32 累加器触发 `Cc overflow`。
- ③ 数据依赖循环流水 —— **否决/中性**：slot 外提、fp16 transpose、reduce 双子块一轮改动全部在噪声内，拒绝合入。

round2 追加（case7 专攻，0.5954 → 0.6815）实测结论：

- `_delta_kernel` 改 (bn, chunk) 仿射网格 + ROB 128→64 + 去 padding 行 `tl.where`（0.092 → 0.054 ms；ROB=128 会 ub overflow）。
- 搬运型 kernel（`_reduce_kernel` / `_fused_kernel`）program 数 `nc = 2*n_aic`：128MB copy 微基准 NC=20 → 1.18 TB/s、NC=40 → 2.29 TB/s（1.94x）；cube 密集 kernel 无此收益。
- 建表 78µs 中约 30µs 为小 dot 的 cube 固定时延，不可无损消除；`tl.cumsum`（0.13 ms）/ 3D broadcast-sum（0.17 ms）变体更慢，选 2D-dot 前缀（0.095 ms）；`tl.atomic_add` 建表在该后端直接 aivec error，禁用。
- 仍未实施：partial 降 fp8 / k-v 驻 L2 重算、手写 CV 流水（PIPE_STAGES=2，天花板约再 1.5-2x）。

## 小算子时延下限与调试判据（910B3 实测）

**小 dot 的 cube 固定时延**：块选择表构建 kernel 78µs 中约 30µs 是小 dot 的 cube 固定时延，不可无损消除（triton_ascend 3.6.0 / 910B3 实测）。同功能前缀计数实现对比：`tl.cumsum` 0.13 ms、3D broadcast-sum 0.17 ms、2D-dot 前缀 0.095 ms——选 2D-dot。`tl.atomic_add` 建表在该后端直接 aivec error，禁用。实测案例见 [BlockSparseAttentionGrad 实现手册](../../runbooks/performance/sparse_attention_grad_optimization.md)。

**调试判据**：输出 buffer 用 `torch.empty` 分配且未被 kernel 全覆盖写时，精度失败应先怀疑覆盖率（未写区域是脏数据）而非数值精度——先核 kernel 写出索引是否覆盖全部输出元素，再排查数值路径。

## Program 数 = DMA 并行流数（910B3 实测）

搬运型 kernel 的 GM 带宽随 program 数（grid）增长，超过物理核数仍有显著收益。同一 128MB copy kernel（[64,128] fp16 tile，triton_ascend 3.6.0 / Ascend 910B3 实测）：

| program 数 NC | 实测带宽 |
|---|---|
| 20（= n_aic） | 1.18 TB/s |
| 40（= 2 × n_aic） | 2.29 TB/s（1.94x） |

结论：大块连续搬运型 kernel（reduce/partial、delta、elementwise 归约）以 `nc = 2 * n_aic` 起步再扫；cube 密集 kernel 无此收益（瓶颈在 cube↔vector 同步时延，不吃 DMA 吞吐）。

## L0C（Cc）容量边界（cube 累加器，910B3 实测）

Cube 累加器驻留 L0C（910B 为 128KB）。两个 [128,128] fp32 累加器（2 × 64KB）即触发 `Cc overflow`：dk/dv 类双累加器 kernel 的输出行 `BT=128` 不可用，需降到 BT ≤ 64；`tl.dot(a, b, acc)` 3 参形态可把累加器放上 cube 复用，但 dk/dv 双输出仍各占一个累加器，BT=128 时两个 [128,128] fp32 累加器仍触发 Cc overflow，实际生效的修复是降 BT。

