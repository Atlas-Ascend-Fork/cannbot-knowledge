---
type: Optimization
title: "X120: 行和与加权归约同趟合并（avg-free fused xn）"
description: "「先求行均值再按行加权累加」的两段式实现会让 avg 落 GM；在同一 UB 驻留内合并行和与加权累加，并配 2D 整块 DMA，可把读次数从 4N 降到 3N。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/vector_compute/ub_fusion_vector_compute.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/adv_api/normalization/LayerNorm.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x120.json
    role: evidence
created_at: "2026-10-27T00:00:00Z"
updated_at: "2026-10-27T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 X120）。
>
> 原始元数据：
>
> ```yaml
> id: X120
> origin: discovered
> confidence: single_op
> op_families: [reduction, elementwise, attention, cv-mix]
> bottlenecks: [undersize_transfer, mte2_stall, no_overlap, l2_cache_thrash]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/disc_x120.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x120.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# Strategy X120: 行和与加权归约同趟合并（avg-free fused xn）

## 核心思路

「先求每行均值 avg[c]，再用 avg[c] 加权累加 xn[p]」的两段式实现里，**avg 是行内归约，只需要这一行
自己的数据**。所以当该行正躺在 UB 里时，「求行和」与「按行加权累加」能在同一次驻留内完成，
avg 不必落 GM 再被下一阶段读回：

```
avg[bg,c] = (1/HW) * S_c, S_c = sum_p x[c,p] # 只依赖本行
xn[bg,p] = sum_c avg[bg,c] * x[c,p] # 同一次驻留内累加
```

访存 4N（读 x 3 次 + 写 out 1 次）→ **3N**，launch 4 → 2：

- K1：每 (组, 通道块) 扫自己的行 → 行和 + 加权累加 → 只写 xn 分片（1N）
- K2：每组拼分片 → mu/std → sigmoid → `out = x*gate`（读+写 2N）；gate 不落 GM，
 每 task 内重算 ncc 个分片和（O(ncc*HW)，相对 chunk 行数可忽略）

x 总量 ≤ L2（192MB）时 K2 的第二次读命中 L2，有效 HBM 流量进一步压向 2N。

## 配套（缺一不可）

1. **整块 2D DMA**：组内行在 GM 连续，一个 tile 的 nr 行用一条 `DataCopyPad`
 （`blockCount=nr, blockLen=HW*esize, srcStride=dstStride=0`）。**实测语义**：每个 block 在 UB 侧按
 32B 向上取整推进（`dstStride` 按 byte 叠加在自然块距上），故 `strides=0` 时落点行距 = `align32B(HW*esize)`，
 必须与 host 侧 rowStride 一致。tile 目标 8~32KB。
2. **UB 行距与 raw 行距统一**：`rowStride = align(HW, 32/min(esize,4))` 且 `rawStride == rowStride`
 → fp16/bf16→fp32 的 Cast 可整 tile 一条 flat 指令。代价：fp16 小 HW 每行浪费 UB（HW=49 → 128B 槽位 vs 98B 数据）。
3. **ncc 取整波**：`BG*ncc ≈ 3*核数`（BG=2→ncc=64，BG=64→ncc=3），BG*ncc 个 task 均匀铺 48 个 AIV。

## 陷阱（实测）

- VEC 指令访问非 32B 对齐 UB 地址 → vector core exception（packed 布局省 UB 不可行）。
- level-0 mask+repeat 形式（Mul / WholeReduceSum）在本机漏写每 256B 块最后一个元素 → 行乘改
 「每 task 预铺 gateTile + 每 tile 一条 flat Mul(count=nr*rowStride)」，行和用 level-2 逐行 ReduceSum。

## 适用场景

`out = f(统计量(x)) ⊙ x` 的归约+门控链：通道注意力（SE/SK/SGE 系）、per-channel norm、GEMV 链。
判据：kernel 里有「把小向量统计量写回 GM 又被下一 kernel 读回」，且该统计量只依赖当前驻留块。
反例：统计量需跨 task 全局归约（如 softmax 的全局 max）时不能同趟合并。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/disc_x120.json`；引用时请结合上文适用条件与失效边界判断适用范围。

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 问题

形如 `out = f(stat(x)) ⊙ x` 的归约+门控链（通道注意力 SE/SK/SGE、per-channel norm、GEMV 链）
常被写成两段式：先求每行/每通道统计量 `avg[c]` 落 GM，再由下一个 kernel 读回做加权累加 `xn[p]`，
最后由第三个 kernel 做 `x ⊙ gate`。基线 98_SGE 因此读 x 3 次 + 写 out 1 次 = **4N**、4 次 launch、

## 关键代码

```cpp
// 之前：逐行 ReduceSum / GetValue + Muls + Add，avg 与 xn 都落 GM
for (int32_t i = 0; i < nr; ++i) ReduceSum<float>(sLocal[i], f[i * pitch], tmpF, hw);
DataCopyPad(avg[r], sLocal, ...);
for (int32_t i = 0; i < nr; ++i) { const float a = aLocal.GetValue(i);
 Muls(tmp, f[i * pitch], a, hw); Add(acc, acc, tmp, hw); }

// 之后：一条 2D DMA + 同驻留内「行和 → 加权累加」
DataCopyPad(xLocal, x[g * cg * hw + r * hw], {nr, hw * sizeof(T), 0, 0, 0}, pad);
ReduceSum<float>(sLocal[i], f[i * rowStride], tmpF, hw); // 行和（level-2）
Axpy(f[i * rowStride], acc, invHw * sLocal[i], hw); // xn += avg_c * x_c
```