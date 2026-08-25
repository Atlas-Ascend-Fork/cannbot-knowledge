---
type: API
title: AscLoadalignUnpack4
description: 从UB对齐搬入VL/4长度u8数据并unpack到VL长度u32类型，中间位置补0。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_unpack4.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignUnpack4

对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现UNPACK4搬入模式：解压缩模式，按无符号整型u8加载VL/4长度数据，unpack到VL长度u32类型，中间位置补0。 支持三种偏移方式：
函数原型：void asc_loadalign_unpack4(vector_int8_t& dst, __ubuf__ int8_t* src)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignUnpack](asc_loadalign_unpack.md)（`related`）：普通 Unpack 将 VL/2 的 u8/u16/u32 扩成双倍位宽，而 Unpack4 固定把 VL/4 u8 扩成 u32；对比可正确选择扩展倍率与目标布局。
- [AscLoadalignV1Deprecated](asc_loadalign_v1_deprecated.md)（`related`）：旧 asc_loadalign_unpack_v2 的 u8→u32 四倍解包功能由 AscLoadalignUnpack4 替代。
- [AscLoadalignV2Deprecated](asc_loadalign_v2_deprecated.md)（`related`）：废弃接口的 UNPACK4 模式由该专用接口承接，规定 VL/4 u8 搬入并扩成 VL u32。
- [AscLoadalignUnpack4Postupdate](asc_loadalign_unpack4_postupdate.md)（`same_topic`）：《AscLoadalignUnpack4Postupdate》处理“从UB对齐搬入VL/4长度u8数据并unpack到VL长度u32类型，调用后自动更新源地址。”。《AscLoadalignUnpack4》提供“从UB对齐搬入VL/4长度u8数据并unpack到VL长度u32类型，中间位置补0。”，其具体合同或探针直接接入u8→u32 unpack4 对齐加载、post-update 地址推进和显式解包合同。
- [AscLoadalignV3Deprecated](asc_loadalign_v3_deprecated.md)（`same_topic`）：AscLoadalignV3Deprecated 与《AscLoadalignUnpack4》的实质衔接是：废弃 Loadalign V3 应迁移到当前 loadalign/postupdate/广播/解包接口，并保留地址与 UB 限定。
<!-- cannbot:related:end -->
