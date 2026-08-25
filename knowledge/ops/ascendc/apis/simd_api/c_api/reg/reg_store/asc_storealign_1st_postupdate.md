---
type: API
title: AscStorealign1stPostupdate
description: 从矢量数据寄存器搬出第一个元素到UB，忽略mask，接口调用后自动更新目的操作数地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storealign_1st_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscStorealign1stPostupdate

从矢量数据寄存器搬出第一个元素到UB的接口，忽略mask，向dst_align32b中搬运src第一个元素，接口调用后自动更新目的操作数地址。支持数据类型为b8、b16、b32。
函数原型：void asc_storealign_1st_postupdate(__ubuf__ int8_t*& dst_align32b, vector_int8_t src, int32_t offset)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscUpdateAddrReg](../reg_data_types/asc_update_addr_reg.md)（`related`）：AscStorealign1stPostupdate 与《AscUpdateAddrReg》的实质衔接是：AscStorealign1stPostupdate 在仅写首元素后更新地址，非 postupdate/通用 Store 与 AscUpdateAddrReg 明确写回粒度和地址推进两部分契约。
- [reg数据搬出](reg_store.md)（`related`）：AscStorealign1stPostupdate 与《reg数据搬出》的实质衔接是：AscStorealign1stPostupdate 在仅写首元素后更新地址，非 postupdate/通用 Store 与 AscUpdateAddrReg 明确写回粒度和地址推进两部分契约。
- [AscStore](asc_store.md)（`same_topic`）：AscStorealign1stPostupdate 与《AscStore》的实质衔接是：AscStorealign1stPostupdate 在仅写首元素后更新地址，非 postupdate/通用 Store 与 AscUpdateAddrReg 明确写回粒度和地址推进两部分契约。
- [AscStoreAlignPostupdate](asc_storealign_postupdate.md)（`same_topic`）：AscStoreAlignPostupdate 与《AscStorealign1stPostupdate》的实质衔接是：StoreAlignPostupdate 在对齐写回后推进地址，pack/first/non-post 变体、Load postupdate、reg 搬出和 AscUpdateAddrReg 拆解数据分布与地址更新。
- [AscStorealign1st](asc_storealign_1st.md)（`same_topic`）：AscStorealign1stPostupdate 与《AscStorealign1st》的实质衔接是：AscStorealign1stPostupdate 在仅写首元素后更新地址，非 postupdate/通用 Store 与 AscUpdateAddrReg 明确写回粒度和地址推进两部分契约。
<!-- cannbot:related:end -->
