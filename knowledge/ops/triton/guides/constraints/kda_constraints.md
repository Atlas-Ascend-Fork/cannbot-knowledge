---
type: Guide
title: kda 类算子设计约束（分块 delta-rule 线性注意力）
description: KDA/GDN 分块前向（chunk 内 Aqk/L/三角求解 + chunk 间状态 scan）类算子的判别、dot 预算、求逆截断、多右端合并、数值安全与 UB 红线；与 linear_recurrent（逐 token persistent）recurrent（host-loop）的分工。
tags: [task.design, topic.compute.composite, topic.precision, topic.implementation.memory_management, topic.tiling]
status: draft
sources: []
created_at: '2026-10-23T00:00:00Z'
updated_at: '2026-10-23T00:00:00Z'
platforms: [a2]
---

# kda 类算子设计约束（分块 delta-rule 线性注意力）

> 跨类别通用约束见 [global_constraints.md](global_constraints.md)；本卡只列 kda（chunked delta-rule）类别特有条款。
> **证据基础**：锚定算子 `12_ChunkKdaFwd`（`q/k/v/g [1,8192,64,128]`、`beta [1,8192,64]`），Ascend910B2C（物理 NPU6）/ CANN 8.5.1 / torch_npu 2.9.0 / Triton-Ascend 3.2.0，2026-10-22~23 实测；精度经官方 `verify.py` 40 case + mfu case 双通过；性能为 msprof `task_time` kernel 时长，MFU 分母为 bf16 实测峰值 315.45 TFLOPS（4096³ GEMM 标定）。产物与全部消融见 `性能优化/12_优化过程/`。

---

## §0 适用范围与判别

### §0.1 判别特征（满足任意两条即命中本卡）

1. 算法写成**块内矩阵化 + 块间状态递推**：token 维按 C（通常 64）切 chunk；
2. 块内有**两个 gram 矩阵**：`Aqk = tril(qg @ kgqᵀ)`、`L = tril(βkq @ kgqᵀ, -1)`；
3. 块内有**三角求解** `(I+L)⁻¹`（显式 inverse 或 solve_triangular），产出 `w = M·βkq`、`u = M·βv`；
4. 块间有状态 `S [K,V]` 的递推 `S' = gl⊙S + kgt@(u − w@S)`。

家族成员（本库编号）：`12_ChunkKdaFwd`、`13_ChunkKdaWithFusedGateFwd`、`14_ChunkScaledDotKktFwd`、`19/20_ChunkKdaFwdIntra/BwdIntra`、`28_ChunkKdaWithFusedGate`、`30_ChunkGatedDeltaRule`、`31_Gdn2Fwd` 等同构变体。

### §0.2 与相邻卡片的分工（⚠️ 别拿错卡）

| 卡片 | 状态处理 | 并行哲学 |
|---|---|---|
| [linear_recurrent_constraints.md](linear_recurrent_constraints.md) | 每 `(b,vh)` 一份 `[K,V]` fp32 状态**驻留 UB**，T 步逐 token 递推 | 单融合 persistent kernel |
| **本卡（kda）** | 按 C=64 分块，状态**每 chunk 重新物化**（块内矩阵化 + 块间 scan） | 多 kernel 流水 + 块级并行 |
| [recurrent_constraints.md](recurrent_constraints.md) | 状态是向量 | host-loop |

> ⚠️ 本类**不能**套用 linear_recurrent 的 L1.1「单融合 persistent」作为默认：本类的块内 gram/求逆是 dot 密集段，必须让它们以 8192 级 grid 完全并行；强行融合会撞 UB 且变慢（实测见 §5）。

---

## Layer 1 设计约束（首次生成就要全部满足）

### L1.1 ★★★ kernel 分解与 dot 预算（强制）

按「并行度需求」而非「数据流」切 kernel：

```
K1 beta 预转置      grid=(B*M,)      # [B,T,H] -> [B,H,Tp]，供后续连续取列
K2 门控（gate）     grid=(B*H*M,)    # 0 dot；产出 qg/βkq/βv/kqt/kgt/gl
K3 gram             grid=(B*H*M,)    # 2 个独立 dot：[C,K]x[K,C]（Aqk、L）
K4 solve            grid=(B*H*M,)    # 1 个 merged dot：[C,C]x[C,K+V]
K5 状态 scan        grid=(B*H,)      # 4 个 dot/chunk，块间串行
```

**dot 预算**：每个 chunk 的 dot 总数目标 ≤ 6（gram 2 + solve 1 + scan 3~4）。本平台上单个 dot 的固定成本约 0.1~1.45 µs（独立~依赖链），8192 chunk 时每多 1 dot ≈ +0.1~0.5 ms。**任何「把 dot 数从 10 降到 6」的结构性改动，收益都大于调 tile。**

### L1.2 ★★★ `(I+L)⁻¹` 用 Neumann 截断（禁止动态分支）

`L` 严格下三角 ⇒ 幂零（`L^C = 0`）⇒ `(I+L)⁻¹ = Σ_{k<C}(−L)^k` **精确终止**，截断是唯一误差源，余项 `≤ ‖L‖^{r+1}/(1−‖L‖)`：

| r | dot 数 | 余项（实测 max‖L‖₂=0.1065） | 适用 |
|---|---|---|---|
| 1（`I−L`） | **0**（掩码加法） | ~1.3e-2 | 本 benchmark 分布（实测输出误差 ~1e-6） |
| 2（`I−L+L²`） | 1 | ~1.4e-3 | 保守默认 |
| 3（4 dot 链） | 4 | ~1.4e-4 | 仅当 ‖L‖ 可能 >0.3 时 |

- **先测 `max‖L‖₂`**（fp32 torch 原型，遍历全部 case/chunk/head）再选 r；Triton 无动态分支，r 必须编译期固定。
- 起点实现用 r=3（4 个链式 dot）；降到 r=1 在本类实测省 **2.2 ms**（11.5→9.3 ms），是本类第一大杠杆。
- 归一化：`β≤0.1`、`|k|~0.05`、块内衰减 `2^{gk_i−gk_j}≤1` ⇒ `|L_ij|~1e-3`；输入幅度/β 明显更大时先重测。

### L1.3 ★★ 多右端求解必须合并（共享左矩阵）

`w = M·(βkq)` 与 `u = M·(βv)` 共享同一 `M=(I+L)⁻¹`，是「同一方程组、两组右端」。按列拼接 `R=[βkq|βv] ∈ R^{C×(K+V)}`，一次 `M·R = [w|u]`（分配律），FLOPs 不变、dot 调用减半。
- 前提：`K+V` 必须是 2 的幂（K=V=128 → 256 ✓）；
- 前提：右端在 workspace 中**连续排布**（`wrhs[:, 0:K]=βkq`、`wrhs[:, K:K+V]=βv`），一次 block_ptr load；
- 实测：两次独立 dot 3.07 ms → 合并 0.78 ms（终版 solve kernel 0.50 ms），且与原实现逐位一致（`max|a−b|=0`）。

### L1.4 ★★ dot 链成本模型优先于 FLOPs

本平台（910B2C + Triton-Ascend 3.2.0）实测：独立 dot 边际 ~0.09–0.35 µs；**依赖链 dot ~1.45 µs**（前一个 dot 的结果经向量段喂下一个）；program 间不重叠、`num_stages` 无效。
⇒ 设计时优先：①把链上 dot 压到 ≤2 环；②把可并行的 dot 一次性发出；③**不要**为省少量 FLOPs 增加 dot 调用。

### L1.5 ★★ 数值安全三条（本类特有）

1. `ei = exp2(-gk)`，**禁止** `1.0/exp2(gk)`：`gk` 可到 −107（log2），`exp2(gk)` 下溢为 0 时除零 → inf → NaN（实测某版本 40 case 中 37 个出现 NaN）。
2. scan 的状态更新必须用**有界** `kgt = kgqᵀ·gl`（元素 ≤|k|）；把 `gl` 折叠出 dot 的写法 `s = gl*(s + kqt@vnb)` 中 `kqt` 未缩放（可达 2^107），`gk<-128` 时 dot 溢 fp32 → `0*inf = NaN`。
3. `gl` 保持 fp32（可低至 2^-107），不要与 bf16 workspace 混存。

### L1.6 ★★ UB 192KB 红线：C 固定 64、BKX 取整 K

- **C=128 不可行**：`[C,C]` fp32 accumulator（64KB×2）+ 操作数 + 扫描 tile 超 192KB，`bishengir` 在 PlanMemory 后失败（关闭 code-motion/multi-buffer 重试仍失败）。
- 门控 K-panel：`BKX=K`（单 panel）比 `BKX=K/2`（双 panel）快 ~0.15 ms——跨步 load 的行宽从 128B 翻倍到 256B；但再往上（多 head 合并到 512B/1KB 行）会因 `g/gk/e/ei` 四个 `[C,2K]` fp32 tile 超 UB 而不可行。
- 全融合（gate+gram+solve 一个 kernel）**不要做**：UB 溢出或变慢（实测 +0.3~0.5 ms）。

### L1.7 ★★ 搬运与布局

- 跨步输入（`[B,T,H,K]` 单 head，行宽 256B/行距 16KB）与输出（同型）用 `tl.make_block_ptr`；gate 实测 `MTE2 55.5%` 是最大单点，block_ptr + BKX=K 合计省 ~0.35 ms。
- workspace 按**消费顺序**连续化：`βkq|βv` 一个缓冲；`qg` 与 `βkq` 同缓冲的上下半区。
- `tl.trans` 只做一次并落到 workspace（`kqt`），scan 侧复用；不要在循环内反复 transpose。
- o 写回用 block_ptr（行距 `H*V`），但本类 o 体量小（16KB/chunk），收益有限。

### L1.8 ★ 精度校验口径（本类踩过坑）

- **mfu_test 单 case 的输出量级可能只有 ~1e-4，远小于 1.56e-2 绝对容差——全零实现也能通过**。候选实现必须以**原多 case（本库 40 case）官方 verify** 为准，并对可疑改动做逐位对拍（`max|a−b|`）。
- 曾因脚本拼接丢失 kernel 段（gram/solve 未写），mfu case 一路"通过"，直到 40 case 才暴露 NaN/错误——**逐位对拍是唯一可靠闸门**。

### L1.9 ★ 零 carry 快速路径必须带运行时守卫

当 chunk 间 carry `gl⊙S` 可忽略时，`v_new=u`、`o=Aqk@u`，scan 可完全并行（详见 pattern 卡 [guarded_zero_carry_fast_path.md](../../optimizations/patterns/guarded_zero_carry_fast_path.md)）。
- 守卫：`Bmax/(1−gl_max) < 2e-2`，其中 `B=kgt@u` 从真实数据算（不是经验常数）；
- **必须保留精确 scan 回退**（慢衰减、`initial_state`、`output_final_state` 时启用）；
- 本算子实测：纯精确 3.862% MFU → 守卫快速路径 **5.152%**。

---

## 实现骨架与代码（canonical 位置）

本卡只承载类别级硬约束，不含实现骨架与代码。以下内容由对应卡片 canonical 维护，命中时一并加载：

- [../operator_playbooks/kda__chunk_kda_fwd.md](../operator_playbooks/kda__chunk_kda_fwd.md) —— **Layer 2 算法骨架 + Layer 3 关键代码** + 实现优先序（本类的唯一 canonical 骨架位置）
- [../../optimizations/patterns/guarded_zero_carry_fast_path.md](../../optimizations/patterns/guarded_zero_carry_fast_path.md) —— 守卫式零 carry 快速路径的改写方法与守卫实现
- [../../optimizations/patterns/multi_rhs_shared_left_merge.md](../../optimizations/patterns/multi_rhs_shared_left_merge.md) —— 多右端合并的公式、布局要求与合法性前提
- [../../runbooks/performance/chunk_kda_fwd_mfu.md](../../runbooks/performance/chunk_kda_fwd_mfu.md) —— 实测轨迹、kernel 拆解、配置梯度与失败路线

## §5 阈值证据（Layer 1 门槛的实测依据）

以下数字只用于支撑 Layer 1 的门槛判定；完整性能轨迹与配置档位见 runbook。

| 约束 | 证据 |
|---|---|
| L1.2 求逆截断 | 40 case 全 chunk/head `max‖L‖₂ = 0.1065`，单 chunk `gk ∈ [-107, 0]`（log2）；r=1 余项 ~1.3e-2，实测输出误差 ~1e-6（该分布下） |
| L1.4 dot 成本 | 独立 dot 0.09–0.35 µs、依赖链 ~1.45 µs、elementwise [128,128] ~0.8 µs（910B2C/NPU6 实测） |
| L1.6 UB 红线 | C=128 与 gate+gram+solve 全融合均在 `bishengir` PlanMemory 后失败（关闭 code-motion/multi-buffer 重试仍失败） |
| L1.7 搬运 | gate vector 核 `MTE2` 占 55.5%；block_ptr + BKX=K 合计 ~0.35 ms |
| 端到端参考 | 11.610 ms / MFU 1.995% → 4.497 ms / 5.152%（口径：73.082 GFLOP、bf16 实测峰值 315.45 TFLOPS、msprof warmup5/repeats5；详见 runbook） |

## 相关

- [linear_recurrent_constraints.md](linear_recurrent_constraints.md) —— 逐 token persistent 形态（对照）
- [recurrent_constraints.md](recurrent_constraints.md) —— host-loop 形态
- [global_constraints.md](global_constraints.md) —— 跨类别通用约束
- [../../optimizations/patterns/guarded_zero_carry_fast_path.md](../../optimizations/patterns/guarded_zero_carry_fast_path.md) —— 零 carry 守卫快速路径
- [../../optimizations/patterns/multi_rhs_shared_left_merge.md](../../optimizations/patterns/multi_rhs_shared_left_merge.md) —— 共享左矩阵的多右端合并
- [../operator_playbooks/kda__chunk_kda_fwd.md](../operator_playbooks/kda__chunk_kda_fwd.md) —— 12_ChunkKdaFwd 单算子实现手册
- [../../../../contrib/ascendc/runbooks/performance/p135_delta_rule_inverse_divide_conquer.md](../../../../contrib/ascendc/runbooks/performance/p135_delta_rule_inverse_divide_conquer.md) —— Ascend C 侧的 delta-rule 求逆分治（对角前代 + 非对角 cube MM），与 L1.2 的 Neumann 截断互补
