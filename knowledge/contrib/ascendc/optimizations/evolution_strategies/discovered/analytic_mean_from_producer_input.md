---
type: Optimization
title: "已验证方案：把「中间张量的通道均值」解析重建为「生产者输入的列和 + 小 GEMV」"
description: "把「中间张量的通道均值」解析重建为「生产者输入的列和 + 小 GEMV」，避免对最大中间张量做完整列和扫描；适用于均值只依赖生产者输入的归约与门控链。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.compute.reduction
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceSum_interface/ReduceSum.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/adv_api/normalization/LayerNorm.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/analytic_mean_from_producer_input.json
    role: evidence
created_at: "2026-10-26T00:00:00Z"
updated_at: "2026-10-26T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 analytic-mean-from-producer-input）。
>
> 原始元数据：
>
> ```yaml
> id: analytic-mean-from-producer-input
> op_families: [matmul, cv-mix, reduction, attention]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/analytic_mean_from_producer_input.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/analytic_mean_from_producer_input.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# 已验证方案：把「中间张量的通道均值」解析重建为「生产者输入的列和 + 小 GEMV」

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 问题现象
`a[b,c] = mean_{k,n}( x_all[b,k,n,c] )`，其中 `x_all` 由 `y = mlp1(xq)` 做空间位移后堆叠而来。
基线为了这个只有 `[B,C]` 大小的向量，对最大的中间张量 `y`（最大 4.27 GB）做了一次**完整列和扫描**：

## 方案（精确，非近似）
`a` 是 `y` 的**线性泛函**，而 `y` 又是 `x` 的线性泛函，于是可以跳到生产者输入上算：

```
Σ_{n<N} y[b,n,j] = Σ_c Sx[b,c]·w1[j,c] + N·b1[j], Sx[b,c] = Σ_{h,w} x[b,c,h,w]
```

位移只改变"哪些行参与"，所以每个 quarter 的全和 = 上面的 Total 加一个边界修正。
边界修正项本身也是 `x` 的线性泛函（bias 在差里抵消）：

```
U = w1·( Σ_h x[b,·,h,0] − Σ_h x[b,·,h,W−1] )
V = w1·( Σ_w x[b,·,0,w] − Σ_w x[b,·,H−1,w] )
branch0: q0:+U[c]+V[C+c] q1:−U[c]−V[C+c] q2:+V[c]+U[C+c] q3:−V[c]−U[C+c]
branch1: 同上但 q0/q1 与 q2/q3 的 U/V 互换 branch2: 0
```

落地三段：
1. **`s2_xstat`**（替换 pad_copy）：x 一次扫描 → 逐 (b,c) 行 `N` 元素连续 DMA → fp32 逐块累加 →
 32B 对齐成对树归约（降到 8 元素后标量折叠）→ 写 `stats[b,c]=Sx/(3N)`；顺手完成 pad copy，
 保证 x 只读一次；
2. **`s2_statsg`**（新增 fp32 小 matmul）：`M=align(B,16)`、`N=3Cp`、`K=Cp`，把 `b1/3` 折进 N 轴 bias，
 一次算出 `Σ_c Sx·w1[j,c]` 的全部 j；
3. **colsum 只跑边界行集**（`nChunks=0`），`reduce_a` 改由 `statR` 合成。

## 精度验证

精度判据与逐 case 结果见证据包；正文只保留机制与适用边界。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/analytic_mean_from_producer_input.json`；引用时请结合上文适用条件与失效边界判断适用范围。

## 有效范围
- 任何「中间张量只用来算一个降维统计量（均值/列和/通道和），而该统计量可由生产者输出线性表出」的结构；
- 判据：kernel 里出现一次对最大中间张量的全量 reduce，且该 reduce 的结果 shape 远小于中间张量；
- 非目标：统计量含非线性（max / softmax / 方差需要二阶矩时要另推）。