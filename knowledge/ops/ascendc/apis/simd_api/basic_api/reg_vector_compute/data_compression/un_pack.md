---
type: API
title: UnPack
description: 将源操作数低半或高半部分元素以高位填0或保持符号位方式扩充位宽写入目的寄存器。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/data_compression/UnPack.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# UnPack

头文件路径为："basic_api/reg_compute/kernel_reg_compute_pack_intf.h"。

对于无符号整型，将源操作数srcReg中低半部分或高半部分的元素以高位填0扩充位宽的方式写入dstReg。对于有符号整型，将源操作数srcReg中低半部分或高半部分的元素以保持符号位扩充位宽的方式写入dstReg。

参数：T: 目的操作数数据类型。 源操作数和目的操作数的数据类型约束参考见表 源操作数和目的操作数的数据类型对应表。；U: 源操作数数据类型。；part: 枚举类型，用于控制读取srcReg的低半部分还是高半部分。 • HighLowPart::LOWEST，低位模式，读取srcReg的低半部分。 • HighLowPart::HIGHEST，高位模式，读取srcReg的高半部分。 注：RegTraitNumTwo只支持LOWEST模式。；S: 目的操作数RegTensor类型。；V: 源操作数RegTensor类型。；dstReg: 目的操作数。 类型为RegTensor。；srcReg: 源操作数。 类型为RegTensor。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [B16 结果大幅偏差 — UNPACK 后补 Reg Cast](../../../../../runbooks/precision/b16_unpack_requires_numeric_cast_before_fp32_compute.md)（`exemplifies`）：《B16 结果大幅偏差 — UNPACK 后补 Reg Cast》说明Reg 的 B16 UNPACK/PACK 只改变寄存器布局，不替代数值格式转换；显式使用预定义 CastParam trait 完成 B16↔fp32。；《UnPack》说明将源操作数低半或高半部分元素以高位填0或保持符号位方式扩充位宽写入目的寄存器。。二者在B16 UNPACK/PACK只改变寄存器分布，显式Reg Cast才做数值转换；Cast trait、lane宽度和边界转换卡共同验证这条链上存在可执行的直接衔接。
- [AscLoadalignUnpack](../../../c_api/reg/reg_load/asc_loadalign_unpack.md)（`related`）：LoadAlignUnpack 把对齐搬入与 unpack 融合，适合从 UB 读取时减少独立步骤。
- [AscLoadalignUnpack4Postupdate](../../../c_api/reg/reg_load/asc_loadalign_unpack4_postupdate.md)（`related`）：《AscLoadalignUnpack4Postupdate》处理“从UB对齐搬入VL/4长度u8数据并unpack到VL长度u32类型，调用后自动更新源地址。”。《UnPack》提供“将源操作数低半或高半部分元素以高位填0或保持符号位方式扩充位宽写入目的寄存器。”，其具体合同或探针直接接入u8→u32 unpack4 对齐加载、post-update 地址推进和显式解包合同。
- [Pack](pack.md)（`related`）：Pack 取低位压缩到目标寄存器半区，UnPack 从半区读出并按零扩展或符号扩展恢复位宽，二者构成布局压缩/展开的直接逆向链。
- [AscUnpack](../../../c_api/reg/data_compress/asc_unpack.md)（`same_topic`）：C API asc_unpack 与 C++ Reg UnPack 共享半区选择和扩展语义，可用于接口迁移。
<!-- cannbot:related:end -->
