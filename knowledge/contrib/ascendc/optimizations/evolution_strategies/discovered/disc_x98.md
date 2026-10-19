---
type: Optimization
title: "GEMM K 轴恒等重排消权重 repack（K 序 (kk,ci)->(ci,kk) 使 repack 布局与原生 W 恒等，cube 直读 W，整段 repack kernel+workspace+cache 移除）"
description: "把 GEMM 的 K 轴序从 (kk,ci)（k = kkci_g + ci）改为 (ci,kk)（k = cik_dim + kk），使经典 repack 布局 wk[co][cik+kk] 与原生 W[co][ci][kk] 逐字节恒等——cube GEMM 直接以 W 为 A 操作数（a_st…"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.neighborhood.convolution
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# Strategy X98: GEMM K 轴恒等重排消权重 repack

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> schema_version: okf.v1
> kind: discovered_strategy
> id: X98
> title: "GEMM K 轴恒等重排消权重 repack（K 序 (kk,ci)->(ci,kk) 使 repack 布局与原生 W 恒等，cube 直读 W，整段 repack kernel+workspace+cache 移除）"
> origin: discovered
> discovered_round: 3
> discovered_from: "6_ConvStandard1d evolution round_3/parallel_2 (node sv3, open_exploration)（compat 副本，真源见 OKF）"
> base_speedup: "1.1290x -> 1.3540x canonical（+19.9%，round_3/paired_recheck_d2 同窗复测 1.3540 / agent 自窗 1.3694 双窗互证）；探针上限（仅跳 repack）1.19x，实测超出因 k_st tight-64 同步收缩"
> confidence: single_op
> status: active
> op_families: [convolution, conv1d, conv2d, matmul]
> bottlenecks: [scalar_compute, mte3_stall, launch_overhead, memory_bound]
> tags: [weight-repack-elimination, k-axis-reorder, layout-identity, cube-direct-read, im2col-gemm, launch-reduction, lru-cache-antipattern, conv, 910b2c]
> strategy_ids: [X98, X14, X22, X23]
> reuse_stats:
>   ops: [6_ConvStandard1d]
>   families: [convolution]
>   passed: 1
> ```

## 判定信号

im2col+GEMM 流水线的卷积（或任何「每 call 把权重 W repack 成 GEMM A 操作数布局」的算子）：
- repack kernel 独立发射（4 发射之一），msprof 上 `aic_mte2_ratio` 极低（~0.04，纯固定开销形态）；
- repack 布局为 `wk[co][k*ci_g+kk]`（K 轴序 (kk,ci)，先 tap 后通道）而原生权重为 `W[co][ci][kk]`
  （先通道后 tap）——**两者仅是 K 轴遍历序不同**；
- 计时 harness 下 repack 缓存（LRU）命中率 ~0%（每 case 每进程只计时一次、weight storage 全新），
  缓存方案本质无效，每 call 全量 repack。

## 核心思路

把 GEMM 的 K 轴序从 `(kk,ci)`（k = kk*ci_g + ci）改为 `(ci,kk)`（k = ci*k_dim + kk），
使经典 repack 布局 `wk[co][ci*k+kk]` 与原生 `W[co][ci][kk]` **逐字节恒等**——
cube GEMM 直接以 W 为 A 操作数（`a_stride=ci_g*k_dim`、`a_batch=co_g*ci_g*k_dim`），
**对任意 k（1/2/3...）生效**。repack kernel、wk workspace、LRU cache 从 launch 流整体移除
（extern "C" 符号保留以兼容链接）。k_st tight 打包可同步收缩（去掉为 repack 布局服务的
+bias 折叠行与 per-tap ci 填充），bias 下沉 epilogue；im2col 仅改行索引（跨 tap 行距
m_st→k*m_st），UB tile 与 DMA 体积不变。

## 适用场景

- **算子类型**: im2col+GEMM 卷积（conv1d/conv2d，grouped/dense）、任何 per-call 权重 repack 的 GEMM 流水线
- **瓶颈类型**: repack 独立发射的固定开销（小 shape 每 call 省一次 launch + 全量 repack 往返）、
  repack 缓存命中率 ~0% 的无效缓存、wk workspace 的 GM 物化
- **不适用**: repack 布局与原生 W 无法通过 K 轴序交换恒等（如含 fp16 hi/lo 分裂、per-k 不同的变换）
- **预期收益**: geomean +20% 级（小 case 主导的 case 集）；大 case 受 repack 带宽占比限制收益变小

## 实现要点

1. 先实证缓存命中率（探针日志），确认"缓存优化"是死路——恒等重排是结构性替代，不依赖命中
2. K 轴序交换后逐 case 验证 A 操作数地址公式（a_stride/a_batch 以 ci_g*k_dim 为步长基）
3. bias 若原折叠进 repack 布局的 +1 行，须改由 epilogue 添加（与 flip 路径一致）
4. im2col 行索引公式同步改（跨 tap 行距 ×k），**勿漏 flip/非 flip 路径守卫**（实测坑：
   重写时丢失 flip 路径 im2col 的 `!flip` 守卫会读未定义 xcol，回归 Bug）
5. 发射合并（X14）可与本策略叠加：repack 消除后剩余 prep/im2col/GEMM/epilogue 再合并

## 平台坑

- 一个 .cpp 只能一个 MIX 入口（X14 坑，107000）
- 双缓冲事件流水（XRDY/XWAR）在 910B2C 本工具链死锁 507034，勿引入手写跨块事件流水

## 来源

自动发现于第 3 轮进化，算子 6_ConvStandard1d（node sv3, open_exploration），
canonical 1.1290x→1.3540x（+19.9%），50/50 精度 PASS，round_3/paired_recheck_d2 同窗复测互证。
