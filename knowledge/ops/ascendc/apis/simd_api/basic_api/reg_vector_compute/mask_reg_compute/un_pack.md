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

- [半精度索引错位—拆分双 int32 掩码](../../../../../runbooks/precision/b16_value_mask_must_split_for_two_int32_index_registers.md)（`exemplifies`）：“用 `UnPack<LOWEST/HIGHEST>` 得到两组 int32 store mask”与“将源操作数src的低半部分或高半部分，展开到目的操作数dst”把双 index mask 配方连接到 UnPack 的低半/高半接口语义。
- [Pack](pack.md)（`same_topic`）：根据所选的低位模式或高位模式，将源操作数src的低半部分或高半部分，展开到目的操作数dst。；根据所选的低位模式或高位模式，将源操作数src的偶数位bit，提取到目的操作数dst的低半部分或高半部分。。UnPack 将半区每 bit 展开，而 Pack 将偶数 bit 压回指定半区；二者在同一 MaskReg 位布局上形成互逆的数据表示操作，联合阅读可设计展开和回收链。
<!-- cannbot:related:end -->
