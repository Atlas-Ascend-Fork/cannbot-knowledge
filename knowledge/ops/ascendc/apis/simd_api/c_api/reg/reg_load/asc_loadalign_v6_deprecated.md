---
type: API
title: asc_loadalign (废弃)
description: reg数据搬运接口，适用于从UB搬入MaskReg。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_v6_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_loadalign (废弃)

reg数据搬运接口，适用于从UB搬入MaskReg。
函数原型：void asc_loadalign(vector_bool& dst, __ubuf__ uint32_t* src)
约束：offset在缺省时默认偏移值offset=0。；用户可以通过自增基地址或者偏移的方式传入offset参数。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalign](asc_loadalign.md)（`same_topic`）：reg数据搬运接口，适用于从UB搬入MaskReg。；将Unified Buffer（UB）中起始地址32字节对齐的数据搬入矢量数据寄存器或掩码寄存器，搬运过程中数据格式和内容保持不变。。废弃接口与当前接口共享从 UB 对齐搬入 MaskReg 的核心能力，当前卡还覆盖矢量寄存器。
<!-- cannbot:related:end -->
