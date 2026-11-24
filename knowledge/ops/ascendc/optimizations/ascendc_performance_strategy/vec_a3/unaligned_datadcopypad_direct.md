---
type: Optimization
title: 非对齐行宽的 kernel 端 DataCopyPad 直通（消除 host F.pad + 切片）
description: 用 DataCopyPad 将非 32B 对齐的 GM 紧凑行直接搬入 UB，尾部 lane 不参与统计和写出
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-unaligned-datadcopypad-direct.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：非对齐行宽的 kernel 端 DataCopyPad 直通（消除 host F.pad + 切片）

单一优化点：行并行 kernel 假定 GM 行 32B 对齐，把非对齐 hidden（如 100 列 fp32）交给 host 侧 `F.pad` 全量拷贝 + 输出 `y[..., :hidden]` 切片。改为 kernel 直接按 `rowStride=hidden` 用 `DataCopyPad` 搬运真实行字节（UB 内自动补齐对齐块），统计只算有效列、store 只写真实行字节，host 免 pad 免切片。

## 1. 原理

- `DataCopyPad` 允许 blockLen 非 32B 对齐：GM 紧凑行（stride=hidden）直接搬入 UB，尾部 lanes 未定义但不进统计、不写出。
- host `F.pad` 的代价 = aten dispatch + 一个全量拷贝 kernel + 输出切片 view（后续消费再拷贝），对小/中 tensor 占端到端 40-70%。
- kernel 端分支 `rowStride == hiddenPad ? DataCopy : DataCopyPad` 对已对齐 shape 零开销。

## 2. 性能问题模式

- python wrapper 存在 `if pad != hidden: F.pad(...); run(...); return y[..., :hidden]` 形态。
- 非对齐 case 的耗时显著高于数据量更大的对齐 case（如 100 列 1024 行慢于 768 列 4096 行）。
- S1/路径分析能定位到 host_pad 分支。

## 3. 正确性红线

- tiling 需新增 rowStride 字段（GM 行步长），kernel 侧缺省回退 hiddenPad（兼容旧布局）。
- UB 尾部垃圾 lanes：统计 mask 只算 hidden_ 列；归一化向量指令可作用全行（含尾列）但 store blockLen=rowStride 只写真实列。
- tiled 多遍扫描模式下行内 tile 起点在非对齐 stride 下错位——该组合必须显式拒绝（TORCH_CHECK）。
- 输出 y = empty_like(x)（真实宽度），消费方免切片。
- DataCopyPad 单块 64KB 上限（blockLen uint16 字节）：超大 rowStride 需分块；bf16/fp16 的 elemSize=2，blockLen 同样以字节计、行宽上限翻倍。

## 4. 泛化条件

- 适用：沿最后一维行处理、行宽非 32B 对齐、host 用 pad 掩盖的归一化/elementwise/归约类 kernel。
- 不适用：行在 GM 非紧凑排布（跨步/索引）或多遍 tiled 扫描架构（除非同步改造 tile 寻址）。

## 5. 实施步骤

1. tiling 加 `int32_t rowStride`；host 计算 `hiddenPad = alignUp(hidden)`（UB 行宽）与 `rowStride = hidden`（GM 步长），接受 `x.size(-1)==hidden` 直传。
2. kernel LoadRow/SubmitRow/StoreRow 按 `rowStride != hiddenPad` 走 `DataCopyPad`（blockLen=rowStride×elemSize 字节；读侧带 `{true,0,0,0}` pad 参数）。
3. 删除 python wrapper 的 F.pad/切片分支；tiled+非对齐组合加显式拒绝。
4. 精度回归：尾列 garbage 不得污染统计（mask 边界）与输出（blockLen 边界）。

## 6. LLM 前置问题

- python wrapper 是否存在 `F.pad + 切片` 分支处理非对齐行宽？
- 非对齐 case 耗时是否反常高于数据量更大的对齐 case（host pad 主导）？
- kernel 是否为沿最后一维的行处理架构（可引入 rowStride 分支）？是否存在 tiled 多遍扫描（需显式拒绝或改造寻址）？
- rowStride×elemSize 是否超过 DataCopyPad 单块 64KB 上限（超大行宽需分块）？

## 7. 验收标准

- build + 精度全过（实测 9/9，P8 maxdiff 7.2e-7 @ fp32 1e-4 容差；尾列 garbage 不污染统计与输出）。
- 实测（P8 = (16,64,100) fp32，Ascend 910B3）：96.4→25.1us（-74%），speedup 2.68→12.60x；对齐 case 全部零退化（分支判断成本不可测）。

## 检索卡（短卡）

动作：用 DataCopyPad 将非 32B 对齐的 GM 紧凑行直接搬入 UB，尾部 lane 不参与统计和写出
适用：沿末维处理紧凑行、行宽非 32B 对齐且 host 以 pad 掩盖的行 kernel
限制：tiling 必须提供 GM 行步长 rowStride；缺省时回退 hiddenPad 以兼容旧布局
范围：末维紧凑行的归一化、elementwise、归约 kernel
检索词：DataCopyPad、blockLen、32B、GM 紧凑行、UB、hiddenPad、rowStride
机会：wrapper 对 hidden 补齐后运行，再以切片返回原始行宽
代价：host 补齐会引入 aten dispatch、全量拷贝 kernel 和输出切片 view
