---
type: API
title: Pack
description: 将源操作数元素的低位部分写入目的寄存器的低半部分或高半部分，实现数据位宽压缩。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/data_compression/Pack.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Pack

头文件路径为："basic_api/reg_compute/kernel_reg_compute_pack_intf.h"。

将源操作数srcReg中的元素选取低8位（对于b16类型）、低16位（对于b32类型）、低32位（对于b64类型）写入dstReg的低半部分或高半部分。

参数：T: 目的操作数数据类型。 源操作数和目的操作数的数据类型约束参考见表 源操作数和目的操作数的数据类型对应表。；U: 源操作数数据类型。；part: 枚举类型，用于控制写入dstReg的低半部分还是高半部分。 • HighLowPart::LOWEST，低位模式，写入dstReg的低半部分。 • HighLowPart::HIGHEST，高位模式，写入dstReg的高半部分。 注：RegTraitNumTwo只支持LOWEST模式。；S: 目的操作数RegTensor类型，由编译器自动推导，用户不需要填写。；V: 源操作数RegTensor类型，由编译器自动推导，用户不需要填写。；dstReg: 目的操作数。 类型为RegTensor。；srcReg: 源操作数。 类型为RegTensor。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [B16 结果大幅偏差 — UNPACK 后补 Reg Cast](../../../../../runbooks/precision/b16_unpack_requires_numeric_cast_before_fp32_compute.md)（`exemplifies`）：《B16 结果大幅偏差 — UNPACK 后补 Reg Cast》说明Reg 的 B16 UNPACK/PACK 只改变寄存器布局，不替代数值格式转换；显式使用预定义 CastParam trait 完成 B16↔fp32。；《Pack》说明将源操作数元素的低位部分写入目的寄存器的低半部分或高半部分，实现数据位宽压缩。。二者在B16 UNPACK/PACK只改变寄存器分布，显式Reg Cast才做数值转换；Cast trait、lane宽度和边界转换卡共同验证这条链上存在可执行的直接衔接。
- [Reg API int8 DIST_PACK_B32 交错零](../../../../../runbooks/precision/reg_api_int8_dist_pack_b32.md)（`exemplifies`）：《Reg API int8 DIST_PACK_B32 交错零》说明Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。；《Pack》说明将源操作数元素的低位部分写入目的寄存器的低半部分或高半部分，实现数据位宽压缩。。二者在DIST_PACK_B32的存储分布与float到int8 Cast、UpdateMask和StoreAlign/Pack位宽必须一致，否则产生隔字节零上存在可执行的直接衔接。
- [UnPack](un_pack.md)（`related`）：Pack 取低位压缩到目标寄存器半区，UnPack 从半区读出并按零扩展或符号扩展恢复位宽，二者构成布局压缩/展开的直接逆向链。
<!-- cannbot:related:end -->
