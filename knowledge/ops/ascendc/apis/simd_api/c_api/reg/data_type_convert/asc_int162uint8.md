---
type: API
title: AscInt162Uint8
description: 将src中int16_t类型元素转换为uint8_t类型并写入dst，支持饱和与非饱和模式，位宽比为2:1。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_int162uint8.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscInt162Uint8

将src中int16_t类型的元素转换为uint8_t类型，并将结果写入dst。支持非饱和与饱和两种模式。

由于源操作数与目的操作数类型位宽比为2:1，写入数据时需要将一个VL大小的数据分为两部分，根据不同接口选择数据写入索引为奇数的位置或偶数的位置。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：int16_t、uint8_t。

约束：mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscUint162uint8](asc_uint162uint8.md)（`related`）：“AscUint162uint8”处理将uint16_t类型数据转换为uint8_t类型，支持饱和与非饱和模式。；“AscInt162Uint8”明确将src中int16_t类型元素转换为uint8_t类型并写入dst，支持饱和与非饱和模式，位宽比为2:1。。实质衔接：保留的窄化接口保持目标 uint8 不变而改变输入符号或位宽，可用于选择正确转换并识别已废弃的 u32 路径。
- [AscInt82int16](asc_int82int16.md)（`same_topic`）：AscInt82int16 与《AscInt162Uint8》的实质衔接是：AscInt8ToInt16 是有符号扩宽，Int16ToUint8 与 Uint8ToUint16 对照方向和符号；Reg int8 pack 故障说明 lane 分布不能按普通连续布局假设。
<!-- cannbot:related:end -->
