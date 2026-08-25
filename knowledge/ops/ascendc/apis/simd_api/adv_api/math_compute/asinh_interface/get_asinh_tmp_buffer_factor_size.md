---
type: API
title: GetAsinhTmpBufferFactorSize
description: 获取Asinh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Asinh_interface/GetAsinhTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetAsinhTmpBufferFactorSize

kernel侧Asinh接口的计算需要开发者预留 申请临时空间，最大临时空间（maxTmpBuffer）和输入所占空间（inputSize * typeSize）存在以下关系： maxTmpBuffer = maxLiveNodeCount * inputSize * typeSize + extraBuffer 其中maxLiveNodeCount表示最大临时空间是输入所占空间的多少倍；extraBuffer表示使用的额外临时空间大小。

函数原型：void GetAsinhTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- maxLiveNodeCount（输出）：最大存活节点数，最大临时空间是输入所占空间的多少倍。
- extraBuf（输出）：使用的额外临时空间大小，单位为字节。

<!-- cannbot:related:start -->
## 相关

- [Asinh](asinh.md)（`related`）：The factor query supports deriving the maximum Asinh tile size from a fixed available workspace.
- [Asinh接口](asinh_interface.md)（`related`）：《GetAsinhTmpBufferFactorSize》明确“获取Asinh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数”；它与《Asinh接口》的“提供Asinh反双曲正弦计算接口及其Tiling临时空间大小查询接口，包含Asinh、GetAsinhMaxMinTmpSize等。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetAsinhMaxMinTmpSize](get_asinh_max_min_tmp_size.md)（`same_topic`）：《GetAsinhMaxMinTmpSize》的任务是“在host侧获取Asinh接口预留临时空间的最大和最小值，用于Tiling参数选择”。《GetAsinhTmpBufferFactorSize》具体提供“获取Asinh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数”，它直接用于Asinh workspace 上下界和 factor 到 Kernel 的同一空间合同。
<!-- cannbot:related:end -->
