---
type: API
title: Pack
description: 根据低位或高位模式，将源操作数src的偶数位bit提取到dst的低半部分或高半部分。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/MaskReg_compute/Pack.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Pack

头文件路径为："basic_api/reg_compute/kernel_reg_compute_maskreg_intf.h"。

根据所选的低位模式或高位模式，将源操作数src的偶数位bit，提取到目的操作数dst的低半部分或高半部分。

参数：part: 枚举类型，低位模式或高位模式。 &bull; LOWEST低位模式； &bull; HIGHEST高位模式。；dst: 目的操作数，类型为MaskReg。；src: 源操作数，类型为MaskReg。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [MaskReg](../register_data_types/mask_reg.md)（`related`）：《MaskReg》给出“MaskReg寄存器用于指示在计算过程中哪些元素参与计算，宽度为RegTensor的八分之一。”；该约束/探针可直接复现、解释或前置验证《Pack》中的“根据低位或高位模式，将源操作数src的偶数位bit提取到dst的低半部分或高半部分。”。
- [UnPack](un_pack.md)（`same_topic`）：《UnPack》明确“根据低位或高位模式，将src的低半部分或高半部分展开到dst，每bit展开为2bit。”；它与《Pack》的“根据低位或高位模式，将源操作数src的偶数位bit提取到dst的低半部分或高半部分。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
