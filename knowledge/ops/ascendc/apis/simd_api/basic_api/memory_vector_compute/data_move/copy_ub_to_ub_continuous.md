---
type: API
title: Copy
description: 支持UB之间的连续数据搬运，数据搬运时格式和内容保持不变。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/Copy_UBToUB_continuous.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# Copy

支持UB之间的连续数据搬运，数据搬运时格式和内容保持不变。

支持Unified Buffer和Unified Buffer之间的连续数据搬运，数据搬运时格式和内容保持不变。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Unified Buffer -> Unified Buffer - VECIN -> VECCALC - VECIN -> VECOUT - VECCALC -> VECIN - VECCALC -> VECOUT - VECOUT -> VECIN - VECOUT -> VECCALC

支持的数据通路：具体支持的数据通路为（以逻辑位置TPosition表示）：

- Unified Buffer -> Unified Buffer
    - VECIN -> VECCALC
    - VECIN -> VECOUT
    - VECCALC -> VECIN
    - VECCALC -> VECOUT
    - VECOUT -> VECIN
    - VECOUT -> VECCALC


本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

参数说明：T：源操作数或者目的操作数的数据类型。支持的数据类型请参考[数据类型](#zh-cn_topic_0000002567699435_section42191353048181)。；isSetMask：参数不生效，保持默认值true即可。；dst：输出 目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。起始地址需要保证32字节对齐。；src：输入 源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。起始地址需要保证32字节对齐。 源操作数的数据类型需要与目的操作数保持一致。；count：输入 参与搬运的元素个数。

约束：位于Unified Buffer的地址必须32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。；isSetMask参数不生效，保持默认值true即可。
