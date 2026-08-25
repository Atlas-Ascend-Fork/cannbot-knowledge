---
type: API
title: AscUnpack
description: 将源操作数低半或高半部分元素扩充位宽后写入目的操作数，支持无符号、有符号及bool类型
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_compress/asc_unpack.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscUnpack

将src中低半部分或高半部分的元素以扩充位宽的方式写入dst，支持
- asc_unpack_lower：取src的低半部分（LOWER），每个元素高位填0扩充位宽后写入dst。
- asc_unpack_upper：取src的高半部分（HIGHER），每个元素高位填0扩充位宽后写入dst。

不同数据类型的扩充方式
- 无符号整型：高位填0扩充。例如vector_uint8_t到vector_uint16_t，src中每个uint8_t元素高位补0扩展为uint16_t。
- 有符号整型：保持符号位扩充。例如vector_int8_t到vector_int16_t，src中每个int8_t元素按符号位扩展为int16_t。
- bool类型（掩码寄存器）：将每bit展开为2bit，高位填0。

矢量数据寄存器unpack流程如图1所示
掩码数据寄存器unpack流程如图2所示

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；dst(输出): 目的操作数（掩码寄存器）。；src(输入): 源操作数（掩码寄存器）。

支持数据类型：int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [B16 结果大幅偏差 — UNPACK 后补 Reg Cast](../../../../../runbooks/precision/b16_unpack_requires_numeric_cast_before_fp32_compute.md)（`exemplifies`）：该卡证明 UnPack 只处理布局/位宽，随后仍需 Cast 才得到 fp32 数值。
- [AscLoadalignUnpack](../reg_load/asc_loadalign_unpack.md)（`related`）：LoadAlignUnpack 把 UB 搬入与解包融合，适合读取阶段减少独立 AscUnpack。
- [AscLoadalignUnpack4Postupdate](../reg_load/asc_loadalign_unpack4_postupdate.md)（`related`）：《AscLoadalignUnpack4Postupdate》处理“从UB对齐搬入VL/4长度u8数据并unpack到VL长度u32类型，调用后自动更新源地址。”。《AscUnpack》提供“将源操作数低半或高半部分元素扩充位宽后写入目的操作数，支持无符号、有符号及bool类型”，其具体合同或探针直接接入u8→u32 unpack4 对齐加载、post-update 地址推进和显式解包合同。
- [AscPackToLow](asc_pack_to_low.md)（`related`）：PackToLow 将低位压入半宽布局，AscUnpack 可从 LOWER/HIGHER 半区按零扩展或符号扩展恢复宽寄存器表示，构成压缩布局的后续展开链。
- [AscStorealignPackPostupdate](../reg_store/asc_storealign_pack_postupdate.md)（`related`）：AscStorealignPackPostupdate 与《AscUnpack》的实质衔接是：PackPostupdate 将低半位压缩写回后推进地址，非 postupdate/quarter/general Store、AscUpdateAddrReg 和 Pack/UnPack 接口拆解同一存储协议。
- [AscUint162uint32](../data_type_convert/asc_uint162uint32.md)（`related`）：uint16 到 uint32 的 1:2 位宽变化需按奇偶半区读取，Unpack 可帮助理解寄存器 lane 展开布局。
- [UnPack](../../../basic_api/reg_vector_compute/mask_reg_compute/un_pack.md)（`related`）：MaskReg UnPack 操作掩码位布局，不等同于数值 RegTensor 扩位；目标寄存器决定选型。
- [asc_pack (废弃)](asc_pack_deprecated.md)（`related`）：AscUnpack 执行 Pack 的逆向扩展，可用于验证高/低半区选择是否保持布局。
- [AscPackToHigh](asc_pack_to_high.md)（`same_topic`）：AscPackToHigh 与《AscUnpack》的实质衔接是：AscPackToHigh 与 PackToLow/Unpack 定义高低半部压缩布局，带 pack 的 store 与 postupdate 入口说明压缩结果如何对齐写回。
- [AscUnsqueeze](asc_unsqueeze.md)（`same_topic`）：AscUnsqueeze 与《AscUnpack》的实质衔接是：AscUnsqueeze 按 mask 逆展开压缩数据，Unsqueeze 是对应基础入口，Squeeze/AscSqueeze 是生成压缩流和 mask 的逆向前置操作。
- [UnPack](../../../basic_api/reg_vector_compute/data_compression/un_pack.md)（`same_topic`）：C API asc_unpack 与 C++ Reg UnPack 共享半区选择和扩展语义，可用于接口迁移。
<!-- cannbot:related:end -->
