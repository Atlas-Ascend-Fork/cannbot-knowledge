---
type: API
title: AscUint82uint16
description: 根据mask将uint8_t类型元素转换为uint16_t类型并写入dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_uint82uint16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscUint82uint16

根据mask将源操作数src中的每个uint8_t类型元素转为uint16_t类型，结果写入dst。由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。参考伪代码

参数：`dst`(输出): 目的操作数（矢量数据寄存器）。；`src`(输入): 源操作数（矢量数据寄存器）。；`mask`(输入): 掩码寄存器，用于控制各元素是否参与计算。mask中与元素对应的比特位为1时，该元素参与计算；为0时，该元素不参与计算。

支持数据类型：uint16_t、uint8_t。

约束：- src与dst的数据类型需要与函数原型匹配。
- mask掩码位为0时，dst对应元素置0。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscInt82int16](asc_int82int16.md)（`same_topic`）：AscInt82int16 与《AscUint82uint16》的实质衔接是：AscInt8ToInt16 是有符号扩宽，Int16ToUint8 与 Uint8ToUint16 对照方向和符号；Reg int8 pack 故障说明 lane 分布不能按普通连续布局假设。
- [asc_uint82uint32 (废弃)](asc_uint82uint32_deprecated.md)（`same_topic`）：焦点处理废弃 uint8→uint32 转换的分级扩宽替代路径；AscUint82uint16正文说明“根据mask将uint8_t类型元素转换为uint16_t类型并写入dst”。候选提供 uint8→uint16→uint32 的可用扩宽链，并用逆向/有符号旧接口说明布局差异。
<!-- cannbot:related:end -->
