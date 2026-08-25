---
type: API
title: UnPack
description: 根据低位或高位模式，将src的低半部分或高半部分展开到dst，每bit展开为2bit。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/MaskReg_compute/UnPack.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# UnPack

头文件路径为："basic_api/reg_compute/kernel_reg_compute_maskreg_intf.h"。

根据所选的低位模式或高位模式，将源操作数src的低半部分或高半部分，展开到目的操作数dst。展开方式为：将每bit展开为2bit，高位置零。

参数：part: 枚举类型，低位模式或高位模式。 &bull; LOWEST低位模式； &bull; HIGHEST高位模式。；dst: 目的操作数，类型为MaskReg。；src: 源操作数，类型为MaskReg。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [半精度索引错位—拆分双 int32 掩码](../../../../../runbooks/precision/b16_value_mask_must_split_for_two_int32_index_registers.md)（`exemplifies`）：本卡明确用 UnPack<LOWEST/HIGHEST> 把 value mask 拆为低、高两半；接口定义该拆分行为。
- [AscLoadalignUnpack4Postupdate](../../../c_api/reg/reg_load/asc_loadalign_unpack4_postupdate.md)（`related`）：《AscLoadalignUnpack4Postupdate》处理“从UB对齐搬入VL/4长度u8数据并unpack到VL长度u32类型，调用后自动更新源地址。”。《UnPack》提供“根据低位或高位模式，将src的低半部分或高半部分展开到dst，每bit展开为2bit。”，其具体合同或探针直接接入u8→u32 unpack4 对齐加载、post-update 地址推进和显式解包合同。
- [AscUnpack](../../../c_api/reg/data_compress/asc_unpack.md)（`related`）：MaskReg UnPack 操作掩码位布局，不等同于数值 RegTensor 扩位；目标寄存器决定选型。
- [Pack](pack.md)（`same_topic`）：《UnPack》明确“根据低位或高位模式，将src的低半部分或高半部分展开到dst，每bit展开为2bit。”；它与《Pack》的“根据低位或高位模式，将源操作数src的偶数位bit提取到dst的低半部分或高半部分。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
