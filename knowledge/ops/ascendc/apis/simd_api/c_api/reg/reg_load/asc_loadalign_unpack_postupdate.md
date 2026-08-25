---
type: API
title: AscLoadalignUnpackPostupdate
description: 从UB对齐搬入数据并实现解压缩，调用后自动更新源地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_unpack_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignUnpackPostupdate

对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现解压缩搬入模式并启用Post Update，接口调用后自动更新源操作数地址。
函数原型：void asc_loadalign_unpack_postupdate(vector_int8_t& dst, __ubuf__ int8_t*& src, int32_t offset)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignUnpack](asc_loadalign_unpack.md)（`same_topic`）：Postupdate 变体在完成相同 unpack 对齐加载后还更新源地址，适合循环流式读取；基础变体保持地址不变。
- [AscLoadalignUnpack4Postupdate](asc_loadalign_unpack4_postupdate.md)（`same_topic`）：《AscLoadalignUnpack4Postupdate》处理“从UB对齐搬入VL/4长度u8数据并unpack到VL长度u32类型，调用后自动更新源地址。”。《AscLoadalignUnpackPostupdate》提供“从UB对齐搬入数据并实现解压缩，调用后自动更新源地址。”，其具体合同或探针直接接入u8→u32 unpack4 对齐加载、post-update 地址推进和显式解包合同。
<!-- cannbot:related:end -->
