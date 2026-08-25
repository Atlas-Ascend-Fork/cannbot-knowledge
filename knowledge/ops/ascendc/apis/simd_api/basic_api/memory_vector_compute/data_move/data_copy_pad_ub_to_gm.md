---
type: API
title: DataCopyPad
description: 将数据从UB非对齐搬运至GM。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopyPad_UBToGM.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# DataCopyPad

将数据从UB非对齐搬运至GM。

该接口提供将数据从Unified Buffer非对齐搬运至Global Memory的功能。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Unified Buffer -> Global Memory - VECIN -> GM - VECOUT -> GM - 如图1所示，对于32字节对齐搬运场景，从Unified Buffer读取的所有数据都会搬运至Global Memory。 - 如图2所示，对于非32字节对齐的场景，在读取Unified Buffer数据时会填入dummy假数据，对齐到32B，搬入Global Memory时会将dummy空数据丢弃，从而实现Unified Buffer到Global Memory的非对齐搬运。

支持的数据通路：具体支持的数据通路为（以逻辑位置TPosition表示）：

- Unified Buffer -> Global Memory
    - VECIN -> GM
    - VECOUT -> GM

- 如图1所示，对于32字节对齐搬运场景，从Unified Buffer读取的所有数据都会搬运至Global Memory。
- 如图2所示，对于非32字节对齐的场景，在读取Unified Buffer数据时会填入dummy假数据，对齐到32B，搬入Global Memory时会将dummy空数据丢弃，从而实现Unified Buffer到Global Memory的非对齐搬运。

本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

参数说明：T：操作数的数据类型。各产品支持的数据类型请参考[数据类型](#section4219135304818)。；mode：配置数据搬运模式。PaddingMode类型，定义如下： enum class PaddingMode : uint8_t {     Normal = 0,  // 默认模式，与原有数据搬运格式保持一致，每次数据搬运都会补齐至32字节对齐     Compact,     // 紧凑模式，允许单次搬运不对齐，统一在整块数据末尾补齐至32字节对齐 };；dst：输出 目的操作数，类型为GlobalTensor。 起始地址无地址对齐约束。；src：输入 源操作数，类型为LocalTensor。 起始地址需要保证32字节对齐。；dataCopyParams：输入 搬运参数，DataCopyExtParams类型，具体参数说明请参考[表3](#table_ub2gm_pad_3)。

约束：位于Unified Buffer的源地址必须32字节对齐，位于Global Memory的目的地址必须1字节对齐。；DataCopyExtParams结构体参数的值需在取值范围内：；
