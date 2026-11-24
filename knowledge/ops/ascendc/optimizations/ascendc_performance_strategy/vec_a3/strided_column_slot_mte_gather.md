---
type: Optimization
title: strided 列数据 32B 槽位 MTE 搬运
description: 将 db<32 的逐元素标量 GM 读取，改为以 32B 槽位通过 DataCopyExtParams 搬运。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-strided-column-slot-mte-gather.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：strided 列数据 32B 槽位 MTE 搬运

> 单一优化点：排序/归约维度非末轴（列元素按 innerStride 散布在 GM）且 dtype 字节宽 <32
> 时，把逐元素标量 GM 读（GetValue ~70ns/次）替换为 32B 槽位批量 MTE 搬运 + 标量从 UB
> 槽位 gather，实测 2.4~4.5x 加速。

## 1. 原理

- MTE2/MTE3 burst 写 UB 按 32B 粒度：db<32 的逐元素 burst（blockLen=db）会让 dst 前进
  db 字节 → 非对齐 → 相邻元素错位（不可用，本策略的核心动机）。
- **32B 槽位搬运**：`DataCopyExtParams{blockCount=n, blockLen=32, srcGap=inner*db-32,
  dstGap=0}`——blockLen=32 字节 + dstGap=0 使 dst 每 burst 恰好前进 32B（恒 32B 对齐），
  槽位 i 的首 db 字节即目标元素（其余字节丢弃）。
- 搬入 UB 后标量 gather 列元素，读 UB 延迟远低于 GM。

瓶颈类型：scalar_heavy（dim≠末轴的 strided 输入逐元素标量 GM 读）。

## 2. 性能问题模式

- 算子的排序/归约维度非末轴（innerStrideElems>1），列元素按 innerStride 散布在 GM。
- 逐元素 `gmX.GetValue`（PIPE_S 标量 GM 读，~70ns/次）成为性能地板（毫秒~秒级 case）。
- dtype 字节宽 db < 32（fp16/fp32/int32/bf16 等），无法用整元素 strided MTE burst 直接搬。

## 3. 正确性红线

- MTE2/MTE3 burst 写 UB 按 32B 粒度：db<32 的逐元素 burst（blockLen=db）会让 dst 前进
  db 字节 → 非对齐 → 相邻元素错位（不可用）。
- 多核 + 标量 SetValue 写 GM 存在 64B cache-line 竞争（不能靠解除退单核守卫换并行）。
- 末元素必须单独小 burst 防 GM 越界（DDR OOB → 507015）。
- 批间双向同步（S→MTE2、MTE2→S）缺一不可：每 tile 只允许单批（curDimElems ≤ 1024；
  多批循环在 910B3 实测硬件级不安全，507015，与 dtype 无关）。

## 4. 泛化条件

- **适用**：dim≠末轴、inner*db ≥ 32、db<32 的 strided 输入；curDimElems ≤ 1024 可单批化。
- **不适用**：inner*db < 32（槽位窗口放不下一列）：回退标量；dimSize < 2：无多批问题但
  收益趋零；TopK 计算主导的 dtype（fp32 大 k）降 dimUbFactor 换单批会净退化（TopK 次数
  ×4）。

## 5. 实施步骤

1. **32B 槽位搬运**：`DataCopyExtParams{blockCount=n, blockLen=32, srcGap=inner*db-32,
   dstGap=0}`，槽位 i 的首 db 字节即目标元素（其余字节丢弃）。
2. **末元素单独 1 burst**（blockLen=db）避免 GM 读越界（DDR OOB → 507015）。
3. 槽位缓冲固定 1024 槽（32KB），**每 tile 只允许单批**（curDimElems ≤ 1024）。
4. 搬完 `MTE2_S` 同步后标量从 UB 槽位 gather 列元素；批循环开头加 `S_MTE2` 反向同步
   （上批 gather 未读完不得覆写 slotBuf）。
5. ES2 叠加 topkTmpBuf 时注意 UB 总量（192KB），必要时 host 降 dimUbFactor 到 1024
   保证单批（仅对 CopyIn 主导的 Cast 路径 dtype；TopK 计算主导的 dtype 降 tile 会退化）。

## 6. LLM 前置问题

- 归约/排序维度是否非末轴（innerStrideElems>1），inner*db 是否 ≥32？
- dtype 字节宽是否 <32（无法整元素 strided MTE burst 直接搬）？
- curDimElems 是否 ≤1024，能否单批完成（多批循环硬件级不安全）？
- UB 预算（含 topkTmpBuf 等）是否容纳 32KB 槽位缓冲？

## 7. 验收标准

- build + 精度全过；实测效果（910B3, TopK）：
- fp32 [1009,1021] dim=0：99.1ms → 22.1ms（4.5x）
- int32 3D [363,367,373] dim=1：3.85s → 1.12s（3.4x）
- fp16 3D：225ms → 73ms（3.1x）；bf16：273ms → 115ms（2.4x）
- int32 [8192,8192] dim=0（ES2+dimUbFactor=1024 单批化）：237ms → 81ms（2.92x）

## 检索卡（短卡）

动作：将 db<32 的逐元素标量 GM 读取，改为以 32B 槽位通过 DataCopyExtParams 搬运。
适用：dim 非末轴、inner×db≥32、db<32；curDimElems≤1024 时可单批处理。
限制：inner×db<32 时槽位窗口容不下一列，须回退。
范围：排序或归约维度非末轴的 strided 输入读取。
检索词：strided 列、32B 槽位、MTE2/MTE3、DataCopyExtParams、srcGap
机会：非末轴列元素在 GM 中跨步散布，并由 PIPE_S 逐元素读取。
