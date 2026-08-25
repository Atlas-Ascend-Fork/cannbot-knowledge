---
type: API
title: AscGetSqueezeStatus
description: 读取squeeze操作后保存的有效数据长度值。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_squeeze_status.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscGetSqueezeStatus

读取squeeze操作后保存至AR特殊寄存器的有效数据长度值，用于配合asc_squeeze_and_storeunalign接口获取已连续搬出的有效数据量。
函数原型：int64_t asc_get_squeeze_status()
返回值：返回int64_t类型的squeeze有效数据长度值。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscSqueezeAndStoreunalign](../reg/reg_store/asc_squeeze_and_storeunalign.md)（`related`）：《AscGetSqueezeStatus》说明读取squeeze操作后保存的有效数据长度值。；《AscSqueezeAndStoreunalign》说明从矢量数据寄存器中筛选有效元素后按非32B对齐地址连续搬出到UB，通过AR寄存器累加偏移实现自动地址管理。。二者在Squeeze有效长度由带status的压缩/搬出操作写入，再由AscGetSqueezeStatus读取；普通Squeeze并不等价上存在可执行的直接衔接。
- [AscSqueezeAndStoreunalignInit](../reg/system_variables_access/asc_squeeze_and_storeunalign_init.md)（`related`）：《AscGetSqueezeStatus》说明读取squeeze操作后保存的有效数据长度值。；《AscSqueezeAndStoreunalignInit》说明对AR特殊寄存器清零，用于配合asc_squeeze_and_storeunalign进行地址自动偏移，首次调用前需初始化。。二者在Squeeze有效长度由带status的压缩/搬出操作写入，再由AscGetSqueezeStatus读取；普通Squeeze并不等价上存在可执行的直接衔接。
- [Squeeze](../../basic_api/reg_vector_compute/compare_and_select/squeeze.md)（`related`）：《AscGetSqueezeStatus》说明读取squeeze操作后保存的有效数据长度值。；《Squeeze》说明将srcReg中被mask选择的有效元素依次复制到dstReg中连续排列，剩余位置置0。。二者在Squeeze有效长度由带status的压缩/搬出操作写入，再由AscGetSqueezeStatus读取；普通Squeeze并不等价上存在可执行的直接衔接。
- [系统变量](system_variables.md)（`related`）：《AscGetSqueezeStatus》说明读取squeeze操作后保存的有效数据长度值。；《系统变量》说明SIMD C API系统变量类接口汇总，提供架构版本、核编号、循环计数器、CTRL寄存器等系统变量的查询与设置。。二者在Squeeze有效长度由带status的压缩/搬出操作写入，再由AscGetSqueezeStatus读取；普通Squeeze并不等价上存在可执行的直接衔接。
- [AscSqueeze](../vector_compute/asc_squeeze.md)（`same_topic`）：AscGetSqueezeStatus说明读取squeeze操作后保存的有效数据长度值。
- [AscSqueezeWithStatus](../reg/compare_and_select/asc_squeeze_with_status_deprecated.md)（`same_topic`）：《AscGetSqueezeStatus》说明读取squeeze操作后保存的有效数据长度值。；《AscSqueezeWithStatus》说明已废弃接口，请使用asc_squeeze_and_storeunalign。将src中被mask选择的有效元素依次复制到dst并连续排列，会将有效数据大小保存至AR寄存器供搬出时使用。。二者在Squeeze有效长度由带status的压缩/搬出操作写入，再由AscGetSqueezeStatus读取；普通Squeeze并不等价上存在可执行的直接衔接。
- [asc_get_ar_spr (废弃)](asc_get_ar_spr_deprecated.md)（`same_topic`）：废弃 asc_get_ar_spr 卡明确要求改用 AscGetSqueezeStatus；两者都读取 squeeze 操作写入 AR 的有效数据长度，后者是当前接口。
<!-- cannbot:related:end -->
