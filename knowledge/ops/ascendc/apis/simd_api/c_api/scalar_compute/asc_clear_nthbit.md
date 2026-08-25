---
type: API
title: AscClearNthbit
description: 将一个uint64_t整数的第idx位设置为0，其余位保持不变。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_clear_nthbit.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscClearNthbit

位操作函数，用于将一个uint64_t整数bits的第idx位设置为0。
函数原型：uint64_t asc_clear_nthbit(uint64_t bits, int64_t idx)
返回值：执行计算得到的结果（uint64_t类型）。
约束：当idx > 63或者idx < 0时，计算逻辑是：(idx % 64 + 64) % 64，得到结果位，设置结果位为0。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [AscSetNthbit](asc_set_nthbit.md)（`related`）：SetNthBit 与 ClearNthBit 对同一 bit 做相反更新，可组成状态位写入与清理。
- [asc_clz（标量计算）](asc_clz.md)（`related`）：ClearNthBit 需要正确位编号，AscClz 等位查询可用于构造位置和验证结果，但不执行更新。
<!-- cannbot:related:end -->
