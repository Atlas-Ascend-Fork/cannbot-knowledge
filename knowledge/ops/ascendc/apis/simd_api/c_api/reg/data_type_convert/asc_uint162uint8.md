---
type: API
title: AscUint162uint8
description: 将uint16_t类型数据转换为uint8_t类型，支持饱和与非饱和模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_uint162uint8.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscUint162uint8

将uint16_t类型数据转化为uint8_t类型，无舍入模式，支持饱和/非饱和模式。

关于饱和/非饱和模式
由于源操作数与目的操作数类型位宽比为2:1，写入数据时需要将一个VL大小的数据分为两部分，根据不同接口选择数据写入索引为奇数的位置或偶数的位置。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：uint16_t、uint8_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。
- 当数据写入目的操作数索引为奇数的位置，索引为偶数位置的数值置零。反之亦然。
- 开启饱和模式和非饱和模式时，需配置ctrl寄存器，ctrl寄存器

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscInt162Uint8](asc_int162uint8.md)（`related`）：“AscUint162uint8”处理将uint16_t类型数据转换为uint8_t类型，支持饱和与非饱和模式。；“AscInt162Uint8”明确将src中int16_t类型元素转换为uint8_t类型并写入dst，支持饱和与非饱和模式，位宽比为2:1。。实质衔接：保留的窄化接口保持目标 uint8 不变而改变输入符号或位宽，可用于选择正确转换并识别已废弃的 u32 路径。
- [AscUint162uint32](asc_uint162uint32.md)（`related`）：uint16 到 uint8 是窄化而非无损升宽，需要额外关注截断与饱和语义。
- [asc_uint322uint8 (废弃)](asc_uint322uint8_deprecated.md)（`related`）：“AscUint162uint8”处理将uint16_t类型数据转换为uint8_t类型，支持饱和与非饱和模式。；“asc_uint322uint8 (废弃)”明确将uint32_t类型数据转换为uint8_t类型，支持饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。 由于源操作数与目的操作数类型位宽比为4:1，写入数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。。实质衔接：保留的窄化接口保持目标 uint8 不变而改变输入符号或位宽，可用于选择正确转换并识别已废弃的 u32 路径。
- [asc_uint82uint32 (废弃)](asc_uint82uint32_deprecated.md)（`same_topic`）：焦点处理废弃 uint8→uint32 转换的分级扩宽替代路径；AscUint162uint8正文说明“将uint16_t类型数据转换为uint8_t类型，支持饱和与非饱和模式”。候选提供 uint8→uint16→uint32 的可用扩宽链，并用逆向/有符号旧接口说明布局差异。
<!-- cannbot:related:end -->
