---
type: API
title: AscLoadDev
description: 不经过DCache直接从Global Memory地址读取整型数据，避免多核操作未对齐Cache Line时的数据覆盖问题。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_load_dev.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadDev

不经过DCache直接从GM地址读取整型数据。 当多核操作GM地址且数据无法对齐到Cache Line时，经过DCache读写可能引入Cache Line粒度的数据覆盖。此时，可使用本接口绕过DCache读取GM数据。
函数原型：int8_t asc_load_dev(__gm__ int8_t* addr)
返回值：从GM读取的数据，返回值的数据类型与addr指向的数据类型一致。
约束：仅支持整型数据，不支持浮点类型。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 训练系列产品等

<!-- cannbot:related:start -->
## 相关

- [AscStoreDev](asc_store_dev.md)（`related`）：不经过DCache向GM地址上写数据。 当多核操作GM地址时，如果数据无法对齐到Cache Line，经过DCache的方式下，由于按照Cache Line大小进行读写，会导致多核数据随机覆盖的问题。此时，可以采用不经过DCache直接读写GM地址的方式，从而避免上述随机覆盖的问题。；不经过DCache直接从GM地址读取整型数据。 当多核操作GM地址且数据无法对齐到Cache Line时，经过DCache读写可能引入Cache Line粒度的数据覆盖。此时，可使用本接口绕过DCache读取GM数据。；两接口闭合绕过 DCache 的 GM 写入与读取路径。
<!-- cannbot:related:end -->
