---
type: API
title: AscSetAtomicAdd
description: 对后续目的地址为GM的数据搬运指令开启原子累加，将待搬运数据与GM已有数据求和后写入GM。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/simd_atomic/asc_set_atomic_add.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSetAtomicAdd

原子累加过程：将待搬运到GM的数据和GM上已有数据进行求和，然后将求和结果写入GM。本接口对后续目的地址为GM的数据搬运指令开启原子累加，不同产品支持的数据搬运通路请参考约束说明。 接口可选择不同的函数原型来设定不同的累加数据类型。
函数原型：void asc_set_atomic_add_int8()
约束：各个产品由于硬件架构不同，支持的数据通路也不同，具体情况如下：；Ascend 950PR/Ascend 950DT，支持的数据通路为UB/L0C Buffer->GM。；Atlas A3 训练系列产品/Atlas A3 推理系列产品，支持的数据通路为UB/L0C Buffer/L1 Buffer->GM。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [AscSetAtomicNone](asc_set_atomic_none.md)（`related`）：AscSetAtomicAdd 开启后会影响后续 GM 搬运，AscSetAtomicNone 是文档要求的状态清理动作，二者构成成对的启用/复位协议。
- [AscAtomicAdd](../scalar_compute/asc_atomic_add.md)（`same_topic`）：AscAtomicAdd：AscAtomicAdd、SIMT asc_atomic_add 与基础 AtomicAdd执行同一 GM 原子累加；SetAtomicAdd/AscSetAtomicAdd则控制后续搬运累加，需避免混淆即时原子与搬运配置。 目标卡《AscSetAtomicAdd》补充：对后续目的地址为GM的数据搬运指令开启原子累加，将待搬运数据与GM已有数据求和后写入GM。
- [SetAtomicAdd](../../basic_api/atomic_operations/set_atomic_add.md)（`same_topic`）：AscSetAtomicAdd 与 Basic API SetAtomicAdd 都配置后续 GM 搬运的原子加模式，是同一随路原子状态在 C/C++ 接口层的对应入口。
<!-- cannbot:related:end -->
