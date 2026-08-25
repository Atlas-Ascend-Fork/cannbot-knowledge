---
type: API
title: asc_ffz（标量计算）
description: 获取一个uint64_t类型数字的二进制表示中从最低有效位开始的第一个0出现的位置，如果没找到则返回-1。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_ffz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# asc_ffz（标量计算）

获取一个uint64_t类型数字的二进制表示中从最低有效位开始的第一个0出现的位置，如果没找到则返回-1。
函数原型：int64_t asc_ffz(uint64_t value)
参数：value（输入）：输入数据，数据类型是uint64_t。
返回值：value中第一个0出现的位置。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [CountLeadingZero](../../basic_api/scalar_compute/count_leading_zero.md)（`related`）：CLZ 从高位统计前导零，而 FFZ 返回首个零位置；选择取决于扫描方向和结果语义。
- [asc_ffs（标量计算）](asc_ffs.md)（`related`）：FFS 找第一位 1，FFZ 找第一位 0；二者共享位编号约定但搜索目标相反。
- [AscZeroBitsCnt](asc_zero_bits_cnt.md)（`same_topic`）：AscZeroBitsCnt 与《asc_ffz（标量计算）》的实质衔接是：AscZeroBitsCnt 是 64 位零位计数；GetBitCount/popc、前导零和 ffz 提供总位数/零位置的邻近位操作，用于避免把计数与定位混淆。
- [GetSFFValue](../../basic_api/scalar_compute/get_sff_value.md)（`same_topic`）：《GetSFFValue》说明查找uint64_t数值二进制表示中从最低有效位开始的首个指定比特值位置，未找到则返回-1。；《asc_ffz（标量计算）》说明获取一个uint64_t类型数字的二进制表示中从最低有效位开始的第一个0出现的位置，如果没找到则返回-1。。二者在GetSFFValue按countValue查最低位首个0或1，asc_ffs与asc_ffz分别对应这两个可执行分支上存在可执行的直接衔接。
<!-- cannbot:related:end -->
