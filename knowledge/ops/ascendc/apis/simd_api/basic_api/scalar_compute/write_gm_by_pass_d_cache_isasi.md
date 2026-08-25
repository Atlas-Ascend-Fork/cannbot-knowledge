---
type: API
title: WriteGmByPassDCache
description: 不经过DCache向GM地址写入数据，可避免多核Cache Line数据覆盖问题。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/scalar_compute/WriteGmByPassDCache_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# WriteGmByPassDCache

头文件路径为："basic_api/kernel_operator_scalar_intf.h"。

不经过DCache向GM地址上写数据。

> [!CAUTION]注意
> 针对NPU架构2201，接口能否将value成功写入GM还与目标地址addr有关，具体

使用场景
- 当多个核写入的数据落在同一条Cache Line内时，经过DCache的读写将以64B为粒度，可能引发多核数据随机覆盖问题（参考DataCacheCleanAndInvalid调用示例3）。使用该接口不经过DCache直接按操作数大小写GM，可避免此问题。
- 经过DCache写GM时可能导致多核间的数据不一致问题（详细原因

由于WriteGmByPassDCache接口向GM写数据时不经过DCache，因此开发者需要考虑如下场景

参数：T: 操作数的数据类型。；addr(输入): 目标GM地址。；value(输入): 待写入目标数据。

支持数据类型：支持的数据类型为int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、int64_t、uint64_t。

约束：针对NPU架构2201，接口是否执行写入取决于目标地址addr在当前128字节对齐区间内的偏移。令，当时，写入生效；当时，不执行写入，目标地址中的数据保持原值。即仅当目标地址位于每个128字节对齐区间的前32字节时，接口才执行写入。

设接口调用前后的目标地址数据分别为和，则

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。
