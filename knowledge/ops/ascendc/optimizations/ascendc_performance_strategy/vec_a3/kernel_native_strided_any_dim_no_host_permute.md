---
type: Optimization
title: 非末轴扫描的 kernel 原生 strided 处理（去宿主 permute）
description: 非末轴改由kernel按原生stride访问，移除宿主permute+contiguous及结果回填转置
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-kernel-native-strided-any-dim-no-host-permute.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：非末轴扫描的 kernel 原生 strided 处理（去宿主 permute）

> 单一优化点：当算子的目标轴不是 innermost 时，不在宿主侧 permute+contiguous
> （两次全量转置 + 依赖框架转置 aclnn 算子），而是把 tensor 分解为
> (outer, scan, inner) 三段，把 inner 长度作为 elem_stride 传给 kernel，
> kernel 内以 strided 视图原生处理任意轴。消除两次全量数据搬移和宿主
> 对框架算子的依赖。

本策略适用于任何"按任意轴作用、输入 contiguous"的算子，与具体算子无关。

---

## 1. 原理

contiguous tensor 按任意 dim 作用时，目标轴的每个"步"的 inner 段
（dim 之后各维的乘积）在 GM 里是连续的。因此 (outer, scan, inner) 分解下：
- scan 步 j、inner 偏移 i 的地址 = outer·scan_len·S + j·S + i；
- 每个 (outer, j) 的 inner 段可用一次（或批量 K 步合并）DataCopyPad 搬运，
  kernel 内做向量更新，running 状态按 inner 列存 UB 向量跨 scan 步存活。

宿主 permute 方案要付：读全量 + 写转置 + 结果再转置回（3 次全量搬移），
且 torch_npu 在 allow_internel_format=False 环境下框架转置算子可能直接
无 bin 可用（aclnn 561103），算子整个不可用。kernel 原生 strided 是
一次搬运零额外转置。

## 2. 性能问题模式

1. 代码形态：host plugin 里出现 `permute(...).contiguous()` + 结果
   `permute(...)` 回填（为把目标轴换到 innermost）；
2. profiling/评测特征：非 innermost 轴的 case 显著慢于 innermost 轴
   （多次全量搬移），或在特定框架环境下直接执行失败；
3. kernel 只支持 innermost 轴、其余全靠宿主转置的"单形态 kernel"。

不适用：输入本身非 contiguous 且无法零拷贝分解（先 contiguous 化更简单）；
inner 维极小（<~128）时 per-step DMA 被固定成本主导，需配合 inner 重分区
（多个核合吃宽切片）。

## 3. 正确性红线

- **stride 语义**：elem_stride 必须 = prod(sizes[dim+1:])（contiguous 输入的
  scan 轴步长），算错则读到错行；
- **tie/NaN 语义**：strided 向量更新的 Select 链必须与 contiguous 路径
  完全一致（EQ(x,x) 检 NaN、<= 取后 index）；
- **写回地址**：values 与 indices 输出与输入同址序（同 (outer,j,inner)
  地址），indices 是 int64（8B）——批量 strided DataCopyPad 的 UB/GM
  stride 按 dtype 分别计算；
- **核间不重叠**：inner 切片按核划分必须不重叠（无需跨核同步的路径），
  边界用精确长度 byte-enabled 写。

## 4. 泛化条件

适用（任一）：
- 任意"按轴"算子（扫描/归约/取值类）作用于非 innermost 轴、输入 contiguous；
- 宿主转置被测出是占比可观的开销（或环境不可用）。

不适用（任一）：
- 输入非 contiguous；
- 算子语义本身要求输出重排（转置即语义）。

## 5. 实施步骤

1. 找到宿主 permute/contiguous 路径，确认目标轴 stride 分解；
2. tiling 结构体加 scan_len / elem_stride（=inner_len）/ outer_len /
   inner_per_core 字段，经 GM buffer 传 kernel；
3. kernel 分派：inner_len==1 走 contiguous 快路径；>1 走 strided 向量路径
   （per-step 向量更新 + K-step 批量 DMA + depth-2 流水）；outer_len==1 且
   长扫描可走行方向 block-scan（无需转置，扫描沿 R）；
4. inner 过窄时 kernel 内重分区（少核宽切片），核数自适应；
5. 全量精度（任意 dim 组合 × dtype）+ 性能验收。

## 6. LLM 前置问题

- 输入是否保证 contiguous？elem_stride 如何从 shape 推出？
- inner 维典型宽度是多少（决定每核切片是否够宽）？
- 是否存在 outer_len==1 且 scan 很长的形态（值得 block-scan 分支）？

---

## 验收标准（实测数据）

以 cummin（910B3）为例：宿主 permute 方案 6/20 case 执行失败（框架转置
aclnn 无 bin）；本策略 20/20 全过，非 innermost case 加速比 0.21~0.83
（case5 [16384,16384] dim=0 0.83x、case10 3D dim=1 0.83x、case14 5D dim=2
1.52x），与高性能参照持平。

## 7. 验收标准

- build + 精度全过（任意 dim 组合 × dtype：elem_stride = prod(sizes[dim+1:]) 语义正确；strided 路径与 contiguous 快路径 tie/NaN 语义一致（EQ(x,x) 检 NaN、`<=` 取后 index）；values 与 indices 同址序写回，indices 按 int64 8B stride 计算；核间 inner 切片不重叠）。
- 性能验收（卡内实测，cummin 910B3）：宿主 permute 方案 6/20 case 执行失败（框架转置 aclnn 无 bin），本策略 20/20 全过；非 innermost case 加速比 0.21~0.83（case5 [16384,16384] dim=0 0.83x、case10 3D dim=1 0.83x、case14 5D dim=2 1.52x），与高性能参照持平。
- 非适用场景（输入非 contiguous、inner 维 <~128 且未重分区、转置即语义）回退原路径且无精度/性能退化。

## 检索卡（短卡）

动作：非末轴改由kernel按原生stride访问，移除宿主permute+contiguous及结果回填转置
适用：contiguous输入上的非innermost轴扫描、归约或取值算子
限制：elem_stride必须等于prod(sizes[dim+1:])，即contiguous输入的扫描轴步长
范围：contiguous张量的任意非末轴按轴kernel路径
检索词：outer-scan-inner、scan_len、elem_stride、inner_len、outer_len
机会：host插件为移轴执行permute+contiguous，并再次permute回填结果
代价：宿主转置开销可观或环境不可用，是另一适用线索。
