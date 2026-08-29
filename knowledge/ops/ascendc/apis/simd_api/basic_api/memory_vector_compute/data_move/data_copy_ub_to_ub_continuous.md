---
type: API
title: DataCopy
description: 支持UB之间的连续数据搬运，数据传输过程中保持原始格式和内容不变。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_UBToUB_continuous.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# DataCopy

支持UB之间的连续数据搬运，数据传输过程中保持原始格式和内容不变。

支持Unified Buffer与Unified Buffer之间的连续数据搬运，数据在传输过程中保持原始格式和内容不变。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Unified Buffer -> Unified Buffer - VECIN -> VECCALC - VECCALC -> VECOUT

支持的数据通路：具体支持的数据通路为（以逻辑位置TPosition表示）：

- Unified Buffer -> Unified Buffer
    - VECIN -> VECCALC
    - VECCALC -> VECOUT


本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

参数说明：T：操作数的数据类型。支持的数据类型请参考[数据类型](#section4219135304818)。；dst：输出 目的操作数。类型为LocalTensor，存储位置为Unified Buffer，目的地址需要32字节对齐。；src：输入 源操作数。类型为LocalTensor，存储位置为Unified Buffer，源地址需要32字节对齐。；count：输入 参与搬运的元素个数。 **注：count * sizeof(T)需要32字节对齐，若未对齐，搬运量会向下取整到32字节对齐。**

约束：位于Unified Buffer的地址必须32字节对齐。；调用连续搬运接口时，count * sizeof(T)需要32字节对齐，若未对齐，则搬运量会向下取整到32字节对齐。；针对如下产品型号：；- Atlas A2 训练系列产品/Atlas A2 推理系列产品
