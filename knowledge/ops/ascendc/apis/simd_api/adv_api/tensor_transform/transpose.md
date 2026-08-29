---
type: API
title: Transpose
description: 对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/tensor_transform/Transpose.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Transpose

对输入数据进行数据排布及Reshape操作。支持多种场景：NZ2ND（1/2轴互换）、NZ2NZ（1/2轴互换）、NZ2NZ（尾轴切分）等。模板参数T支持half/float。

提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。Tiling参数通过Transpose Tiling获取。接口参数：dstTensor输出转置结果；srcTensor输入数据；sharedTmpBuffer临时缓存；transposeInfo含源/目标shape和格式信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [Transpose Tiling](transpose_tiling.md)（`related`）：Tiling参数通过Transpose Tiling获取。；host侧Tiling接口，用于获取Transpose kernel计算所需的Tiling参数，分两步：通过GetTransposeMaxMinTmpSize获取最大和最小临时空间大小；通过GetTransposeNDTilingInfo获取kernel侧所需tiling参数。。Kernel 侧 Transpose 明确消费 Transpose Tiling，目标页给出 Host 侧临时空间查询与 tiling 参数生成的完整前置链。
<!-- cannbot:related:end -->
