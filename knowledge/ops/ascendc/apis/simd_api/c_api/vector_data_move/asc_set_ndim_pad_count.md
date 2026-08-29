---
type: API
title: AscSetNdimPadCount
description: 设置asc_ndim_copy_gm2ub接口各个维度左右侧的padding元素个数。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_set_ndim_pad_count.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSetNdimPadCount

用于设置asc_ndim_copy_gm2ub接口的各个维度左右侧的padding元素个数。
函数原型：void asc_set_ndim_pad_count(asc_ndim_pad_count_config& config)
约束：需配合asc_ndim_copy_gm2ub使用。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscNdimCopyGm2ub](asc_ndim_copy_gm2ub.md)（`related`）：用于设置asc_ndim_copy_gm2ub接口的各个维度左右侧的padding元素个数。；多维数据搬运接口，将数据从Global Memory (GM)搬运到Unified Buffer (UB)。相比于基础数据搬移接口，可以更加自由配置搬入的维度信息。 本功能最多能处理5个维度，每个维度都可以单独配置Stride，且支持随路Padding功能。相关配置参数有很多，需要通过不同的接口传入。 表1 Stride配置涉及的所有参数及其传入接口，其中i表示第i维，可取值［0,4］；PadCount 配置函数直接为 AscNdimCopyGm2ub 提供逐维左右 padding，主搬运接口明确支持随路 Padding。
- [AscNdimPadCountConfig](../struct/asc_ndim_pad_count_config.md)（`related`）：asc_ndim_pad_count_config用于asc_set_ndim_pad_count接口中，设置asc_ndim_copy_gm2ub接口的各个维度左右侧的padding元素个数。；用于设置asc_ndim_copy_gm2ub接口的各个维度左右侧的padding元素个数。；两端分别定义配置结构和写入该结构的设置接口。
<!-- cannbot:related:end -->
