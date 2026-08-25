---
type: API
title: Transpose Tiling
description: 用于获取Transpose Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/tensor_transform/Transpose-Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Transpose Tiling

host侧Tiling接口，用于获取Transpose kernel计算所需的Tiling参数，分两步：通过GetTransposeMaxMinTmpSize获取最大和最小临时空间大小；通过GetTransposeNDTilingInfo获取kernel侧所需tiling参数。

GetTransposeMaxMinTmpSize参数：ascendcPlatform平台信息；srcShape输入shape；typeSize数据类型字节数；isReuseSource预留传false；maxValue/minValue输出临时空间范围。

GetTransposeNDTilingInfo参数：ascendcPlatform平台信息；输入shape各维度；typeSize数据类型字节数；maxTmpSize可用临时空间；tiling输出TransposeTiling结构体。

<!-- cannbot:related:start -->
## 相关

- [AscTranspose](../../c_api/vector_compute/asc_transpose.md)（`same_topic`）：AscTranspose 与《Transpose Tiling》的衔接是：AscTranspose 与基础/高阶 Transpose 共享转置数据布局；LoadDataWithTranspose 可作为上游搬运转置，tiling 与 noTrans 布局案例说明方向参数必须一致。
- [Transpose](transpose.md)（`same_topic`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《Transpose Tiling》明确提供“用于获取Transpose Tiling参数。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
<!-- cannbot:related:end -->
