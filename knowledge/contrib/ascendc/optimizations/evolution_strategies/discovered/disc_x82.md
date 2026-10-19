---
type: Optimization
title: "X82: 门控幅度预算驱动的 sub-chunk 收缩（衰减可分离化）+ V 轴并行"
description: "分块 delta-rule 的 sub-chunk 长度 C 是自由参数（块内是精确的，块间状态递推与 C 无关），但它不是数值自由的：参考实现的 C=64 让 |cumsum(gate)| 在官方 case 上达到 181，此时 exp() 上/下溢，而参考的 clamp(.., max=0) 在…"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.reduction
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# Strategy X82: 门控幅度预算驱动的 sub-chunk 收缩（衰减可分离化）+ V 轴并行

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> id: X82
> origin: discovered
> discovered_round: 1
> discovered_from: round_1/parallel_2 (node x0, open_exploration)
> base_speedup: "vs PyTorch geomean 6.639x(基线) -> 26.9788x; 相对基线 4.06x (asc 329.83us -> 81.16us, 同一 45 case 配对)"
> ```

## 核心思路

分块 delta-rule 的 **sub-chunk 长度 C 是自由参数**（块内是精确的，块间状态递推与 C 无关），
但它**不是数值自由的**：参考实现的 C=64 让 |cumsum(gate)| 在官方 case 上达到 **181**，
此时 `exp()` 上/下溢，而参考的 `clamp(.., max=0)` 在严格下三角上是 no-op。
把 C 按「门控累积幅度预算」收缩到 **16**（实测全 50 case 的最大 |cumsum| 仅 **52.6**）后，

```
decay[i,j] = exp(G[i] - G[j]) = exp(G[i]) * exp(-G[j])
```

**可分离且恒有限**，于是块内计算从「一个 rank-3 衰减张量 [C,C,K] 的 elementwise 乘 + 归约」
塌缩成**四个小 GEMM**（Aqk / Lm / w / u），而不是 [C,C,K] 的三维广播。

配套：**V 是并行轴**——任务 = `(b, hv, v-block)`，状态切片 `S[:, v0:v0+vlen]` 独立演化 ⇒
零核间通信、无 SyncAll、状态全程 UB 常驻（不回 GM）。

## 适用场景

- 分块 delta-rule / 门控线性注意力前向（KDA、GDN、GLA、Mamba2 的逐通道门控分支）
- 序列短（本算子 T ≤ 97，≤2 个 64-chunk）或门控幅度大（gate 经 cumsum 后量级达 10^2）
- 需要在**向量核**上算块内矩阵而形状不足以喂饱 Cube 的 tiny-shape 场景
- 参考实现里出现 `exp2(clamp(gk_i - gk_j, max=0))` 这类 rank-3 衰减张量时，优先检查 C 是否可收缩

## 实现要点

- **先测预算再定 C**：对全量 case 统计 `max |cumsum(gate)|`，取使 `exp(±G)` 不溢出的最大 C。
  本算子 64→16（预算 181→52.6）。C 变小会增加块数（串行段变长），需与块内收益权衡。
- 门控激活的 softplus 路径可写成 `-exp(a_log + ln(softplus(z)))`，避免一次标量 `exp`。
- 每个 sub-chunk 的递推（全部 2D、归约轴显式，无逐元素标量读）：
  ```
  G = cumsum(gamma)   (4 次 log 步进 Add)
  E = exp(G), Ei = exp(-G); Qe = q*E, Ki = k*Ei, Ke = k*beta*E
  Aqk[i,:] = scale*<Qe[i,:], Ki[0:i+1,:]>        (逐行广播 + Mul + ReduceSum AR)
  Lm [i,:] =        <Ke[i,:], Ki[0:i+1,:]>
  X = (I+Lm)^-1 逐行前代                          (Bcast axis-1 + Mul + RS RA)
  w = X@Ke, u = X@(v*beta)
  vn = u - w@S, o = scale*(Qe@S) + Aqk@vn
  S = E_last (*) (S + Ki^T @ vn)
  ```
- **V tile 宽取一个 32B 单位**（`VB = 32/sizeof(T)`），使每个 `DataCopyPad` burst 落在单个对齐单元内。
- shape-exact：全部按真实 `L=min(C, T-sc), Kd, Vd` 计算，K 维 pad 列用 32B 对齐掩码杀掉。
- 硬件约束（踩坑）：`blockCount==1` 的 `DataCopyPad` GM↔UB burst 不得超过一个 32B 单元；
  `blockCount>1` 时 `rightPadding` 必须落在 32B 内。

## 边界

- C 收缩会**增加块数**：块间状态递推是串行段，T 很长时块数×每块固定开销可能反超收益；本算子 T≤97 才成立。
- 精度与参考**逐位不同**（参考的 clamp 在 C=64 下实际生效与否取决于 gate 分布）；须按掩蔽判据验收。
- 本线实测：batch 模式崩溃 507035（仅 per-case 可用），交付前必须解决流安全——见 failure pattern 记录。

## 来源

自动发现于第 1 轮进化，算子 FusedRecurrentKda（910B2C，进化基线内核模式）：
round_1/parallel_2（node x0, open_exploration），asc 329.83us → 81.16us（同一 45 case 配对，4.06x 相对基线；
vs PyTorch geomean 6.639x → 26.9788x）。
