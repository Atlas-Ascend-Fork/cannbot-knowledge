---
type: Optimization
title: step>1 末维切片的行批装配（strided-row-batch-assembly）
description: 将按行×位置切分的微段搬运，改为每核认领连续 outer 行并按 R 行批量装配。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-strided-row-batch-assembly.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：step>1 末维切片的行批装配（strided-row-batch-assembly）

> 单一优化点：slice_scatter/scatter 类"选择拷贝"算子当切片维是最后一维且 step>1 时，按 (行, 位置) 切分会产生海量 2-8B 微段；改为每核认领连续 outer 行区间、按 R 行一批在 UB 内装配，把段开销从 O(outer×D) 段降到 O(outer/R) 批。

- **策略级别**：进阶策略

## 1. 原理

`slice_scatter` / `scatter` 类"选择拷贝"算子满足：切片维是最后一维（inner==1）、step>1（散位写入）、行字节 ≤ UB 预算（~80KB）。此时按 (行, 位置) 切分会产生海量 2-8B 微段，每段一次 MTE + 全流水屏障，段开销乘子可达 19~838×（S1 扫描体积模型量化）。

方案：每核认领连续 outer 行区间；每批 R 行（R=clamp(UB预算/行字节, 1, 256)）在 UB 内批量装配后一次写出。段开销从 O(outer×D) 段×2 屏障 → O(outer/R) 批×3 屏障；GM 读写量 = 理论最小。

- 改动量级：进阶策略

## 2. 性能问题模式

- 算子是 `slice_scatter` / `scatter` 类"选择拷贝"算子，切片维是最后一维（inner==1）、step>1（散位写入）、行字节 ≤ UB 预算（~80KB）。
- 按 (行, 位置) 切分产生海量 2-8B 微段，每段一次 MTE + 全流水屏障，段开销乘子可达 19~838×（S1 扫描体积模型量化）。

## 3. 正确性红线

- **标量装配循环的索引必须经运行时步长**（`base + k*stride`，stride=tiling 里的 step）：若写成仿射连续形式 `dstOff + e`，编译器会**自动向量化**为 VEC local→local copy，其 32B 起始对齐要求在奇数行宽下直接触发 aivec error（错误码 0x400000063/0x70000005a 类）。
- tiling struct 追加字段必须保持 int32-only 布局（设备侧按 word 拷贝）。
- UB 预算：行批 buffer 与流水队列 buffer **按 mode 二选一分配**，两者同时分配会溢出 192KB UB。

## 4. 泛化条件

- **适用**：step>1（散位写入）的末维切片 scatter/slice_scatter；行字节 ≤ UB 预算；L 不太大（L ≤ ~700，否则标量 SetValue 成为新瓶颈）。
- **不适用**：step==1 时行内覆盖是连续的，优先考虑更便宜的连续路径（如 mode3 扁平切分）；L 很大（>~700）时标量 SetValue 成为新瓶颈；inner>1 时原段结构已足够大。

## 5. 实施步骤

每核认领连续 outer 行区间；每批 R 行（R=clamp(UB预算/行字节, 1, 256)）：

1. MTE2 批量连续读 input 行区 → bufA（R×D 元素；input 全张量连续）
2. MTE2 批量连续读 src 行区 → bufB（R×L 元素）
3. PIPE_ALL 后在 UB 内装配 `bufA[i*D+st+k*step] = bufB[i*L+k]`（标量 strided 写）
4. MTE3 一次连续写回整批输出

## 6. LLM 前置问题

- 切片维是否是最后一维（inner==1）且 step>1？行字节是否 ≤ UB 预算？
- 标量装配循环的索引是否经运行时步长（`base + k*stride`）而非仿射连续形式？
- 行批 buffer 与流水队列 buffer 是否按 mode 二选一分配（避免 192KB UB 溢出）？
- L 是否超过 ~700（标量 SetValue 会成为新瓶颈）？

## 7. 验收标准

- build + 精度全过；实测（Ascend 910B3, NPU, iters=50 双源）：
  - P9（bf16, 30 万微段）: 2200→43.9us，**8.4×**
  - P11: 7716→109us，**4.8×**；P20: 72429→1899us，**4.0×**（绝对 38×）；P19: 14409→270us，**1.08×**（绝对 53×）
  - 几何平均贡献 0.540→1.279×；20/20 bit-exact

## 检索卡（短卡）

动作：将按行×位置切分的微段搬运，改为每核认领连续 outer 行并按 R 行批量装配。
适用：step>1 的末维散位写入，行字节不超 UB，且 L≤约700。
限制：装配索引必须使用 tiling 中的运行时 step：base+k×stride。
范围：slice_scatter/scatter 的末维选择拷贝路径。
检索词：末维切片、slice_scatter、行批装配、outer 行、运行时步长、R 行批次
机会：末维 step>1 选择拷贝产生大量 2–8B 微段。
代价：L 过大时，标量 SetValue 会成为新瓶颈。
