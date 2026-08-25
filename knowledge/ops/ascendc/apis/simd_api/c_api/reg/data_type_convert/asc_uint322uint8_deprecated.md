---
type: API
title: asc_uint322uint8 (废弃)
description: 将uint32_t类型数据转换为uint8_t类型，支持饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。
  由于源操作数与目的操作数类型位宽比为4:1，写入数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_uint322uint8_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# asc_uint322uint8 (废弃)

将uint32_t类型数据转换为uint8_t类型，支持饱和/非饱和模式。

关于舍入模式和饱和/非饱和模式
由于源操作数与目的操作数类型位宽比为4:1，写入数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：uint32_t、uint8_t。

约束：- 开启饱和模式和非饱和模式时，需配置ctrl寄存器，ctrl寄存器

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscUint162uint32](asc_uint162uint32.md)（`related`）：焦点处理废弃 uint32→uint8 转换的邻接位宽替代链；AscUint162uint32正文界定“将uint16_t类型数据转换为uint32_t类型”。候选给出逆向转换或 uint32→uint16→uint8 邻接链，避免把无关 dtype 转换当替代。
- [AscUint162uint8](asc_uint162uint8.md)（`related`）：“AscUint162uint8”处理将uint16_t类型数据转换为uint8_t类型，支持饱和与非饱和模式。；“asc_uint322uint8 (废弃)”明确将uint32_t类型数据转换为uint8_t类型，支持饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。 由于源操作数与目的操作数类型位宽比为4:1，写入数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。。实质衔接：保留的窄化接口保持目标 uint8 不变而改变输入符号或位宽，可用于选择正确转换并识别已废弃的 u32 路径。
- [AscUint322uint16](asc_uint322uint16.md)（`related`）：焦点处理废弃 uint32→uint8 转换的邻接位宽替代链；AscUint322uint16正文界定“将uint32_t类型数据转换为uint16_t类型，支持饱和与非饱和模式”。候选给出逆向转换或 uint32→uint16→uint8 邻接链，避免把无关 dtype 转换当替代。
- [asc_int322uint8 (废弃)](asc_int322uint8_deprecated.md)（`related`）：焦点处理废弃 uint32→uint8 转换的邻接位宽替代链；asc_int322uint8 (废弃)正文界定“将int32_t类型转化为uint8_t类型，支持饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。 由于源操作数与目的操作数类型位宽比为4:1，写入数据时需要将一个VL大小的数据分为四部分，根据不同接”。候选给出逆向转换或 uint32→uint16→uint8 邻接链，避免把无关 dtype 转换当替代。
- [asc_uint82uint32 (废弃)](asc_uint82uint32_deprecated.md)（`related`）：焦点处理废弃 uint32→uint8 转换的邻接位宽替代链；asc_uint82uint32 (废弃)正文界定“将uint8_t类型转化为uint32_t类型。 由于源操作数与目的操作数类型位宽比为1:4，读取数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3”。候选给出逆向转换或 uint32→uint16→uint8 邻接链，避免把无关 dtype 转换当替代。
<!-- cannbot:related:end -->
