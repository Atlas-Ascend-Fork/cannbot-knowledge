---
type: API
title: AscInt82half
description: 将int8_t类型数据转换为half类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_int82half.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscInt82half

将int8_t类型数据转换为half类型。

由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：half、int8_t。

约束：mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscHalf2Int8](asc_half2int8.md)（`related`）：AscInt82half 是该转换的反向数据类型通路，可用于核对低/高 half lane 与 int8 lane 的打包布局。
- [AscUint82half](asc_uint82half.md)（`related`）：无符号版本保持目标 half 不变，但输入范围改为 uint8；读取原始字节时必须先确定符号解释。
- [AscInt82half](../../vector_compute/asc_int82half.md)（`same_topic`）：两页实现相同 int8 到 half 转换的 Vector 与 Reg C API 版本，是迁移执行模型时需要对照的核心转换契约。
<!-- cannbot:related:end -->
