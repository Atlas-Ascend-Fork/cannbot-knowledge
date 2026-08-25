---
type: API
title: SetBufferSpace
description: 设置Matmul计算时可用的L1 Buffer/L0C Buffer/Unified Buffer/BiasTable Buffer空间大小，单位为字节。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetBufferSpace.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetBufferSpace

设置Matmul计算时可用的L1 Buffer/L0C Buffer/Unified Buffer/BiasTable Buffer空间大小，单位为字节。

参数：
- l1Size（输入）：设置Matmul计算时，能够使用的L1 Buffer大小，单位为字节。默认值-1，表示使用AI处理器L1 Buffer大小。
- l0CSize（输入）：设置Matmul计算时，能够使用的L0C Buffer大小，单位为字节。默认值-1，表示使用AI处理器L0C Buffer大小。
- ubSize（输入）：设置Matmul计算时，能够使用的UB Buffer大小，单位为字节。默认值-1，表示使用AI处理器UB Buffer大小。
- btSize（输入）：设置Matmul计算时，能够使用的BiasTable Buffer大小，单位为字节。默认值-1，表示使用AI处理器BiasTable Buffer大小。

返回值：-1表示设置失败； 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：《GetTiling》明确“获取Tiling参数。”；它与《SetBufferSpace》的“设置Matmul计算时可用的L1 Buffer/L0C Buffer/Unified Buffer/BiasTable Buffer空间大小，单位为字节。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetFixSplit](set_fix_split.md)（`related`）：《SetBufferSpace》明确“设置Matmul计算时可用的L1 Buffer/L0C Buffer/Unified Buffer/BiasTable Buffer空间大小，单位为字节。”；它与《SetFixSplit》的“设置固定的baseM、baseN、baseK，单位为元素个数。”在实际调用参数、数据流或结果校验上直接衔接。
- [Matmul Tiling类](matmul_tiling.md)（`same_topic`）：《Matmul Tiling类》明确“提供Matmul矩阵乘的Host侧Tiling类，包含TCubeTiling结构体、GetTiling及形状、类型、切分等参数设置方法。”；它与《SetBufferSpace》的“设置Matmul计算时可用的L1 Buffer/L0C Buffer/Unified Buffer/BiasTable Buffer空间大小，单位为字节。”在实际调用参数、数据流或结果校验上直接衔接。
- [Matmul Tiling类使用说明](matmul_tiling_usage.md)（`same_topic`）：《Matmul Tiling类使用说明》给出“Ascend C提供一组Matmul Tiling API，方便用户获取Matmul kernel计算时所需的Tiling参数。用户只需要传入A/B/C矩阵的Position位置、Format格式和DType数据类型等信息，调用API接口，即可获取到Init中TCubeTiling结构体中的相关参数。”；该约束/探针可直接复现、解释或前置验证《SetBufferSpace》中的“设置Matmul计算时可用的L1 Buffer/L0C Buffer/Unified Buffer/BiasTable Buffer空间大小，单位为字节。”。
<!-- cannbot:related:end -->
