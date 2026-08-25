---
type: API
title: AscUint162uint32
description: 将uint16_t类型数据转换为uint32_t类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_uint162uint32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscUint162uint32

将uint16_t类型数据转为uint32_t类型。

由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：uint16_t、uint32_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscInt162Uint32](asc_int162uint32.md)（`related`）：AscUint162Uint32 保持无符号扩宽，但源类型为 uint16；对照可明确本接口的有符号输入转换边界。
- [AscUint162uint8](asc_uint162uint8.md)（`related`）：uint16 到 uint8 是窄化而非无损升宽，需要额外关注截断与饱和语义。
- [AscUint322uint16](asc_uint322uint16.md)（`related`）：AscUint162uint32 是 AscUint322uint16 的反向位宽变换，可用于核对窄化后恢复时的范围与信息损失。
- [AscUnpack](../data_compress/asc_unpack.md)（`related`）：uint16 到 uint32 的 1:2 位宽变化需按奇偶半区读取，Unpack 可帮助理解寄存器 lane 展开布局。
- [asc_uint322uint8 (废弃)](asc_uint322uint8_deprecated.md)（`related`）：焦点处理废弃 uint32→uint8 转换的邻接位宽替代链；AscUint162uint32正文界定“将uint16_t类型数据转换为uint32_t类型”。候选给出逆向转换或 uint32→uint16→uint8 邻接链，避免把无关 dtype 转换当替代。
- [asc_uint82uint32 (废弃)](asc_uint82uint32_deprecated.md)（`same_topic`）：焦点处理废弃 uint8→uint32 转换的分级扩宽替代路径；AscUint162uint32正文说明“将uint16_t类型数据转换为uint32_t类型”。候选提供 uint8→uint16→uint32 的可用扩宽链，并用逆向/有符号旧接口说明布局差异。
<!-- cannbot:related:end -->
