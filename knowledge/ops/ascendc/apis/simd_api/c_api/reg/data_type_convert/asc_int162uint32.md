---
type: API
title: AscInt162Uint32
description: 将src中int16_t类型元素转换为uint32_t类型并写入dst，源操作数与目的操作数位宽比为1:2。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_int162uint32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscInt162Uint32

将src中int16_t类型的元素转换为uint32_t类型，并将结果写入dst。转换过程将16位有符号整数转换为32位无符号整数。

由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：int16_t、uint32_t。

约束：mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscInt162Int32](asc_int162int32.md)（`related`）：AscInt162Int32 与本接口共享 16→32 位扩宽及奇/偶半 VL 选择，差别只在目的有符号性。
- [AscUint162uint32](asc_uint162uint32.md)（`related`）：AscUint162Uint32 保持无符号扩宽，但源类型为 uint16；对照可明确本接口的有符号输入转换边界。
<!-- cannbot:related:end -->
