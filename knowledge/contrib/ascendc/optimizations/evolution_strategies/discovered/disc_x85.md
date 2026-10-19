---
type: Optimization
title: "X85: 冻结参考 max 的延迟归一化在线 softmax（deferred-rescaling）"
description: "标准 FlashAttention 在线 softmax 每个 KV tile 都要维护 running max 并对已累加的 acc_o 做一次rescale：m_new = max(m_old, rowmax(S))；alpha = exp(m_old − m_new)；acc_o = acc_…"
tags:
  - task.optimization
  - topic.attention
  - topic.compute.normalization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# Strategy X85: 冻结参考 max 的延迟归一化在线 softmax（deferred-rescaling）

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> id: X85
> origin: discovered
> discovered_round: 1
> discovered_from: round_1/parallel_2
> base_speedup: 1.0044x (vs PyTorch, 45 artifact-free cases geomean)
> ```

## 核心思路

标准 FlashAttention 在线 softmax 每个 KV tile 都要维护 running max 并对已累加的 `acc_o` 做一次
rescale：`m_new = max(m_old, rowmax(S))`；`alpha = exp(m_old − m_new)`；`acc_o = acc_o·alpha + P@V`；
`sumexp = sumexp·alpha + rowsum(P)`。这一段的代价是**每 tile 一次 [M_tile, d] 的广播乘 + 加**，
是长序列下向量侧最大的单项开销。

本策略利用 softmax 对参考量的**不变性**：整行只取**一个**参考 max `m*`（来自第一个 KV tile 的 rowmax），
后续所有 tile 都用同一个 `m*`：

```
P_t = exp(S_t − m*)        G = Σ_t P_t @ V_t        Sum = Σ_t rowsum(P_t)
out = G / Sum              （exp(−m*) 在除法里整行约掉，与经典式数学恒等）
```

于是运行态累加器**完全不需要逐迭代 rescale**：

- V2 从 `Broadcast(alpha)→[M,d] + Mul(acc_o, alpha_2d) + Add(acc_o, stage_o)` 退化为一条裸 `Add(acc_o, stage_o)`；
  `alpha_ring` / `sumexp_i_ring` / `alpha_2d` 三个缓冲可以直接删除（UB 规划随之重推）。
- `reduce_max` 从每 tile 一次降为每 task 一次（只有 t==0 需要）。
- 每个 KV tile 省掉 `2×M_tile×d` 次向量元素操作 + 一次 `[M_tile, d]` 广播写。以 M_tile=64、d=256 计，
  每 tile 省 32768 次向量元素操作。

## 适用场景

- 流式/分块 softmax 内核（FA / GQA / MLA prefill 与长序列 decode 的 KV 循环）已经在线归一化，
  且**痛点集中在向量侧的 per-tile rescale**（profiling 表现为向量管道占用高、cube 侧与之交替空转）。
- dtype 与 shape 满足数值安全：`S = QK^T·scale` 的幅值上界有**实测证据**且远离 fp32 `exp` 溢出界 88
  （本例 hd≤256 时 max|S| ~ O(10)，σ ≈ √hd/9 ≤ 2，留 30+ 余量）。
- 需要除零安全：`m*` 对应的那一项 `exp(0)=1` ⇒ `Sum ≥ 1`，恒不为零。

## 实现要点

1. **参考量冻结在 t=0**：`m*` 由 `t==0` 的 `rowmax(S_0)` 得到后写入常驻缓冲，循环内不再更新；
   `reduce_max` 只在 `t==0` 执行。
2. **累加器只加不缩**：V2 退化为 `Add(acc_o, stage_o)`；末尾一次 `acc_o /= Sum`。
3. **UB 再规划（关键，否则装不下）**：
   - 逐迭代的 O 暂存 `stage_o[M_tile, d]` 别名到**已死的 S/P tile 区**（V1 与 V2 在同一 AIV 上顺序执行，
     `acc_s`/`tmp` 在 V2 时已无读者）——省下整个 `M_tile·d·4` 的常驻（d=256 时 64KB）。
   - 末尾归一化不要 `[M_tile, d]` 广播缓冲：把 `1/Sum` 变成 `[M_tile, 64]` 行复制，再用带 repeat-stride 的
     `Div(dst, src0, src1, mask=64, repeat=M_tile, {d/8, d/8, 8})`。
4. **保留回退开关**：无 logits 上界证据时**必须**退回经典在线 rescale（或加 clamp）。
   本策略的正确性依赖 `exp(S − m*)` 不溢出，不能无证据使用。
5. **与 UB 瘦身联动**：本策略删掉的 `alpha_ring` / `sumexp_i_ring` / `alpha_2d` 常驻量，
   往往是修复 UB 越界（`ub_total > UB`）所需的那几 KB～几十 KB。

## 来源

自动发现于第 1 轮进化，算子 8_SelfAttention（L4, sijia 编号；Q=K=V=x 的 MHA self-attention，
三段融合 qkv 投影 → FA → out 投影，全链 fp32-core），round_1/parallel_2（open_exploration）。

- 50/50 case 精度 PASS（fp32 名义 max_abs ≤ 5e-8、fp16/bf16 ≤ 3e-5，容差 0.01）。
- 45 例无参考伪影 case 的 geomean speedup = **1.0044x**（vs PyTorch；同 run 的 `median_speedup` = 0.9588，
  剔除了 5 例参考侧 task_time 尖峰伪影）。
- 该变体同时修掉了 archived 基线在本地 case 集上的 `da≥96` UB 越界（`3·HALF_M·da·4 + 133632 > 196608`）
  与 `da>128` 的 host 守卫拒绝，使 35/50 不可运行的基线恢复到 50/50。

## 与既有策略的区别

- **P119**（two-pass → online softmax）：解决"两遍写回"→"单遍流式"，仍**保留**逐 tile 在线 rescale。
- **X38**（GM workspace-ring KV-tile 宽度缩放）：减少 GM ring 往返次数，不动 rescale 结构。
- **canonical `attention-core-vector-softmax-reduction` D4**（删 max 减法直接 exp）：要求删掉**整个**
  max 减法（等价于 `m*=0`），对 logits 上界的要求更强；本策略**保留**一个真实参考 max 并冻结它，
  数值安全边界更宽（只要求 `max|S| − min|S|` 不溢出，而非 `|S|` 本身不溢出）。

## 实现坑（分块路径 / head_dim > 128，两条都只在分块路径暴露）

1. **PV 的 `mma` 必须显式传 `n_actual = kw`**：否则 cube 会从 `kw` 宽的 L0B tile 读 `N = BLOCK_N` 列，
   设备报 `507015 "L0B address exceeds maximum range"`。
2. **分块循环复用同一 L1 tile 时必须补 `MTE1→MTE2` 握手**：现成的 `M_MTE1` flag 只约束 MTE1 管道，
   下一 chunk 的 GM→L1 拷贝会覆盖上一 chunk 的 L1→L0 仍在读的 tile
   —— 这是 `da>128` 四例输出整体偏 ~1e-2 的真凶。
   注意 `da<=128` 的单块路径下这两条都完全不可见，改动 da>128 支持时不能只靠 da<=128 的回归验证。
