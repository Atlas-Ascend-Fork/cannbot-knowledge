---
type: API
title: SetPadValue
description: 设置DataCopyPad非对齐搬运时需要填充的数值，支持GM到UB的填充数据自定义。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move_aux_config/SetPadValue_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetPadValue

设置DataCopyPad非对齐搬运时需要填充的数值，支持GM到UB的填充数据自定义。

该接口提供将数据从Global Memory非对齐搬运至Unified Buffer的功能，可以根据开发者的需要自行填充数据。 当每个搬运的数据块长度（blockLen）非32字节对齐时，每一个数据块都需要填充数据至32字节对齐。 特别地，针对Ascend 950PR/Ascend 950DT，支持Compact模式，该模式支持单个数据块非32字节对齐，将所有数据块合并成一个连续数据块，在该数据块右侧填充数据至32字节对齐。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Global Memory -> Unified Buffer - GM -> VECIN - GM -> VECOUT - GM -> VECCALC（仅Ascend 950PR/Ascend 950DT支持） 填充的数据有两种配置方式： - 配置结构体DataCopyPadExtParams的参数pa

本接口组包含 DataCopyPad（GMToUB非对齐数据搬运）, 逻辑位置TPosition。

本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

约束：结构体DataCopyPadExtParams的参数取值范围需要考虑不要超过UB空间大小。；当DataCopyExtParams结构体参数blockCount、blockLen任意一个值为0时，该接口将被视为NOP（空操作）。该说明针对如下型号生效：；Atlas A3 训练系列产品/Atlas A3 推理系列产品；Atlas A2 训练系列产品/Atlas A2 推理系列产品

支持的硬件型号：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
