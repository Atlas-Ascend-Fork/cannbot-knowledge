---
type: API
title: GetAcoshTmpBufferFactorSize
description: 获取Acosh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Acosh_interface/GetAcoshTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetAcoshTmpBufferFactorSize

kernel侧Acosh接口的计算需要开发者预留 申请临时空间，最大临时空间（maxTmpBuffer）和输入所占空间（inputSize * typeSize）存在以下关系： maxTmpBuffer = maxLiveNodeCount * inputSize * typeSize + extraBuffer 其中maxLiveNodeCount表示最大临时空间是输入所占空间的多少倍；extraBuffer表示使用的额外临时空间大小。

函数原型：void GetAcoshTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：
- typeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- maxLiveNodeCount（输出）：最大存活节点数，最大临时空间是输入所占空间的多少倍。
- extraBuf（输出）：使用的额外临时空间大小，单位为字节。

<!-- cannbot:related:start -->
## 相关

- [Acosh](acosh.md)（`related`）：《GetAcoshTmpBufferFactorSize》明确“获取Acosh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数”；它与《Acosh》的“按元素做双曲反余弦函数计算，输入值域需在1到65504范围内”在实际调用参数、数据流或结果校验上直接衔接。
- [Acoshf](../../../../simt_api/math_functions/float_math_functions/acoshf.md)（`same_topic`）：Acoshf 与《GetAcoshTmpBufferFactorSize》的实质衔接是：Acoshf 是标量双曲反余弦；Acosh 高阶接口及空间查询是 tensor 版本，Coshf 是其反函数，可用于定义域和往返验证。
- [Acosh接口](acosh_interface.md)（`same_topic`）：《Acosh接口》明确“提供Acosh反双曲余弦计算接口及其Tiling临时空间大小查询接口，包含Acosh、GetAcoshMaxMinTmpSize等。”；它与《GetAcoshTmpBufferFactorSize》的“获取Acosh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数”在实际调用参数、数据流或结果校验上直接衔接。
- [GetAcoshMaxMinTmpSize](get_acosh_max_min_tmp_size.md)（`same_topic`）：《GetAcoshMaxMinTmpSize》明确“在host侧获取Acosh接口预留临时空间的最大和最小值，用于Tiling参数选择”；它与《GetAcoshTmpBufferFactorSize》的“获取Acosh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
