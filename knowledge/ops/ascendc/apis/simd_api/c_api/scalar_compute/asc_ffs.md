---
type: API
title: asc_ffs（标量计算）
description: FindFirstSet接口，输入数据的二进制表示中从最低位向最高位查找第一个值为1的位，并返回其位置，如果没找到则返回-1。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_ffs.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# asc_ffs（标量计算）

FindFirstSet接口，输入数据的二进制表示中从最低位向最高位查找第一个值为1的位，并返回其位置，如果没找到则返回-1。
函数原型：int64_t asc_ffs(uint64_t value)
返回值：int64_t类型，输入数据中第一个1出现的位置。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [__ffs（整数数学函数）](../../../simt_api/math_functions/integer_math_functions/_ffs.md)（`related`）：“__ffs（整数数学函数）”处理从二进制输入数据的最低位开始，查找第一个值为1的比特位的位置，并返回该位置的索引，索引从1开始计数；如果二进制数据中没有1，则返回0。；“asc_ffs（标量计算）”明确FindFirstSet接口，输入数据的二进制表示中从最低位向最高位查找第一个值为1的位，并返回其位置，如果没找到则返回-1。。实质衔接：__ffs 与 asc_ffs 都从最低位查找首个 1，但未命中返回值不同，跨编程层迁移时必须核对这一契约。
- [asc_ffz（标量计算）](asc_ffz.md)（`related`）：FFS 找第一位 1，FFZ 找第一位 0；二者共享位编号约定但搜索目标相反。
- [GetSFFValue](../../basic_api/scalar_compute/get_sff_value.md)（`same_topic`）：《GetSFFValue》说明查找uint64_t数值二进制表示中从最低有效位开始的首个指定比特值位置，未找到则返回-1。；《asc_ffs（标量计算）》说明FindFirstSet接口，输入数据的二进制表示中从最低位向最高位查找第一个值为1的位，并返回其位置，如果没找到则返回-1。。二者在GetSFFValue按countValue查最低位首个0或1，asc_ffs与asc_ffz分别对应这两个可执行分支上存在可执行的直接衔接。
<!-- cannbot:related:end -->
