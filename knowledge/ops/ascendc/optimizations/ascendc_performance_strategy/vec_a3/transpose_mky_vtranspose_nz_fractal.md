---
type: Optimization
title: 任意 perm 转置的 MKY 面分解 + UB 内 vtranspose NZ 分形流水
description: 将任意 perm 转置改为 MKY 面分解，并用 vtranspose 的 NZ fractal 路径搬运
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-transpose-mky-vtranspose-nz-fractal.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：任意 perm 转置的 MKY 面分解 + UB 内 vtranspose NZ 分形流水

单一优化点：多维 transpose（纯搬运）中 y 末轴元素在 x 中步进为整行（逐元素 gather，每元素一个 32B MTE 槽，有效带宽 <1%）时，
把任意 perm 分解为「n 轴（x 末轴，天然连续）× k 轴（y 末维来源的 x 维）× m 面（其余维）」，
面内 [k,n]→[n,k] 用「GM 行式大块读 + UB→UB 16x16 NZ 重排 + vtranspose 硬件转置 + strided 块写」四步完成。

## 1. 原理
- 地址分解：y[m,n,k] 的三段视图使 x 面内行 k 步进 xKStride=inStride[pk]、列 n 步进 1；y 面内行 n 步进 yNStride、列 k 步进 1（y 末维）。
- 搬运必须「GM 大块、UB 重排」：vtranspose（两参数 `Transpose<uint16_t>`，硬件内联）要求源/目的为紧凑 16x16（行距 32B）。
  GM 直读 NZ 布局 = 每 32B 一个 burst（碎片），实测比逐元素还慢；正确做法是 CopyIn 按行大块（blockLen=cols*dts）读入行式布局，
  再用 nTile/16 条 UB→UB DataCopy（blockCount=rows, blockLen=32B, srcGap=ubRowBytes/32-1）重排为连续 16x16 块。
- GM 侧 srcStride/dstStride 为字节任意值（无需 32B 对齐）；对齐只约束 UB 布局（vtranspose 16x16 紧凑恒满足）。
- 尾块安全：rows<16 → 脏行转置后落 y 序列 ≥rows，CopyOut blockLen=rows 截断；cols%16≠0 → 脏列落 y 序行 ≥cols，blockCount=cols 截断。无需清零。

## 2. 性能问题模式（代码阅读即可识别）
- 纯搬运算子的泛化路径用「逐元素 32B 槽 gather」（DataCopyPad blockLen=dtypeSize）；
- 2D/多维 perm 使 fastStride=整行长度（如 [1,0]、[2,0,1]、[4,3,2,1,0]）；
- 实测耗时与元素数成正比且远超带宽时间（本例 case7 1023²fp16 1319us vs 带宽时间 ~11us）。

## 3. 正确性红线
- vtranspose 源必须是连续 256 个 uint16（16x16 行距 32B）——GM 直读或行距≠32B 的 UB 布局都会静默产出错位数据；
- m 面基址在 x/y 两侧是不同的线性组合（mStrideX/mStrideY），kernel 内多维混合进制解码必须两侧独立累加；
- 事件同步（SetFlag/WaitFlag 双缓冲）在 TPipe 管理下有 ID 冲突风险（实测曾致 vec core timeout 挂死），保守 PIPE_ALL 正确且开销可忽略；
- 仅 16bit dtype（vtranspose uint16 位视图 bit-exact）；32bit 需 u16 交织（见反例）。

## 4. 泛化条件
适用：任意 rank≥2、任意 perm（n 轴=x 末轴被搬动 perm[q]==rank-1 且 q≠rank-1）、16bit dtype、K>1、N>16、m 维数≤6。
不适用：x 末轴未被搬动（恒等尾段，走连续大块拷贝即可）；32/64bit dtype（vtranspose 无对应位宽，交织需奇偶列 scatter 不可向量化）。

## 5. 实施步骤
1. host tiling 判定 perm/q/pk，计算 K/N/M 与 xKStride/yNStride/mDim/mStrideX/mStrideY；nTile 按 UB 预算（4*stripBytes ≤ UB/2）自适应。
2. kernel strip 循环：m 解码 → CopyIn（1 条 strided 大块）→ PIPE_ALL → NZ 重排（nTile/16 条 UB copy）→ PIPE_ALL → vtranspose ×(nTile/16) → PIPE_ALL → CopyOut（每 16x16 块 1 条 strided）。
3. strip 序号跨核等分（stripsPerCore + 前 rem 核多 1）。

## 6. LLM 前置问题
- 输入末轴是否被搬动？perm 是否使 fastStride 为整行？dtype 是否 16bit？
- K>1 且 N>16？m 维数是否 ≤6？
- UB 预算内 nTile 是否 ≥16？

## 7. 验收标准
- 精度 bit-exact（转置为纯位搬移）；
- 逐元素路径 case 提速 ≥10x（本例 16bit case 全部 12-97x）；已优化 case 不回归。

## 实测数据（Ascend910B3, 2026-08-15）
case7 (1023²fp16) 1319→24us（55x）；case13 (2,7,256,256 bf16) 1108→18us（62x）；case15 (11,13,17,67,67 fp16) 13998→363us（39x）；
case3 (4096²bf16) 19886→205us（97x）；case20 (2,511,2049 fp16) 4318→189us（23x）。

## 检索卡（短卡）

动作：将任意 perm 转置改为 MKY 面分解，并用 vtranspose 的 NZ fractal 路径搬运
适用：rank≥2，x 末轴被移位，16bit，K>1、N>16，且 m 维数≤6
限制：vtranspose 源必须为连续 256 个 uint16，即 16×16 且行距 32B
范围：满足维度与步长条件的 16bit 多维纯搬运 transpose
检索词：transpose、perm、MKY、vtranspose、NZ fractal、xKStride、yNStride、uint16
机会：纯搬运路径逐元素占用 32B gather 槽，且 perm 使 fastStride 成为整行长度
