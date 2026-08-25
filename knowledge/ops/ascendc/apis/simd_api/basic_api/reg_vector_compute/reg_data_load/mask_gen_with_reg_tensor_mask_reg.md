---
type: API
title: MaskGenWithRegTensor
description: 将数据从RegTensor搬运至MaskReg，通过offset参数选择数据块，b16类型每个bit广播为2bit，b32类型每个bit广播为4bit。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_load/MaskGenWithRegTensor_MaskReg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# MaskGenWithRegTensor

头文件路径为："basic_api/reg_compute/kernel_reg_compute_maskreg_intf.h"。

MaskGenWithRegTensor能够实现数据从RegTensor搬运至MaskReg。

- 数据类型为b16时，RegTensor（256B）分成16个数据块（16B），用户通过参数可选择某一个数据块，数据块的每个bit broadcast成2bit后变为32B，即输出的MaskReg。
- 数据类型为b32时，RegTensor（256B）分成32个数据块（8B），用户通过参数可选择某一个数据块，数据块的每个bit broadcast成4bit后变为32B，即输出的MaskReg。

具体搬运原理

参数：T: 源操作数的数据类型。支持的数据类型请参考数据类型。；offset: offset决定了srcReg中需要搬运的数据块，具体描述请参考关键特性说明。 • 当数据类型为b16，offset∈[0, 15]。 • 当数据类型为b32，offset∈[0, 31]。；U: 源操作数的RegTensor类型。例如RegTensor\ ，由编译器自动推导，用户不需要手动填写。；dst(输出): 目的操作数，类型为MaskReg。；srcReg(输入): 源操作数，类型为RegTensor。

支持数据类型：b16、b32。

约束：- 当数据类型为b16，offset∈[0, 15]；当数据类型为b32，offset∈[0, 31]。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 Reg 扫描按 256B 锁定 lane](../../../../../runbooks/precision/dav3510_vector_register_width_is_256_bytes.md)（`exemplifies`）：Ascend950 Reg 扫描按 256B 锁定 lane 与《MaskGenWithRegTensor》的实质衔接是：这些卡共同约束 256B RegTensor 的 lane 数、B16/B32 提升后的 mask 宽度以及 LoadAlign/VF 调用范围；所连错例均由按错误数据宽度计算 lane 或目标 VL 导致。
- [LoadAlign](load_align_mask_reg.md)（`related`）：MaskGen 从 RegTensor 的选定数据块生成 MaskReg，LoadAlignMaskReg 从 UB 搬入 MaskReg；二者按掩码来源是寄存器数据还是内存数据选用。
- [MaskReg](../register_data_types/mask_reg.md)（`related`）：MaskGenWithRegTensor 的输出就是 MaskReg；MaskReg 位宽为 RegTensor 八分之一，解释 b16/b32 bit 广播后的固定 32B 结果。
- [Select](../mask_reg_compute/select.md)（`related`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《MaskGenWithRegTensor》具体提供“将数据从RegTensor搬运至MaskReg，通过offset参数选择数据块，b16类型每个bit广播为2bit，b32类型每个bit广播为4bit。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [AscCreateMask](../../../c_api/reg/reg_data_types/asc_create_mask.md)（`same_topic`）：AscCreateMask 与《MaskGenWithRegTensor》的实质衔接是：AscCreateMask 根据数据位宽和 pat_mode 生成 MaskReg，随后由 UpdateMask/GetMaskSpr、Load/Store 和 MergeMode 消费；两个编译错例限定模板类型与可写引用。
- [StoreAlignMaskReg](../reg_data_store/store_align_mask_reg.md)（`same_topic`）：StoreAlignMaskReg 与《MaskGenWithRegTensor》的实质衔接是：MaskReg Store 的对齐/非对齐形态依赖 MaskReg 生成，LoadAlign 是反向搬入，C API StoreAlign 提供同语义入口。
- [StoreUnAlignMaskReg](../reg_data_store/store_un_align_mask_reg.md)（`same_topic`）：StoreUnAlignMaskReg 与《MaskGenWithRegTensor》的实质衔接是：非对齐 MaskReg Store 依赖 MaskGen/MaskReg 与 UnalignReg 配置，和非对齐 Load 是往返协议；squeeze 初始化卡给出真实配置错误后果。
<!-- cannbot:related:end -->
