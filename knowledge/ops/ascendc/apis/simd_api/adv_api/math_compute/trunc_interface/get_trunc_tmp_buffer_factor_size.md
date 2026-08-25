---
type: API
title: GetTruncTmpBufferFactorSize
description: 获取maxLiveNodeCount和extraBuf，用于推算Trunc接口在固定临时空间下单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Trunc_interface/GetTruncTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetTruncTmpBufferFactorSize

获取Trunc接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetTruncTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [AscTrunc](../../../c_api/reg/data_type_convert/asc_trunc.md)（`related`）：《AscTrunc》说明将浮点数按TRUNC（向零方向截断）截断为整数值，结果保持原浮点类型。；《GetTruncTmpBufferFactorSize》说明获取maxLiveNodeCount和extraBuf，用于推算Trunc接口在固定临时空间下单次最大计算元素数量。。二者在AscTrunc与Memory Trunc、SIMT half/bfloat16/float变体共享向零截断语义，workspace查询用于高阶接口分块上存在可执行的直接衔接。
- [Trunc](trunc.md)（`related`）：GetTruncTmpBufferFactorSize 与《Trunc》的实质衔接是：Trunc 的 factor-size 查询要与 Trunc kernel 及 max/min 空间查询配套，才能按 maxLiveNodeCount/extraBuf 正确反推 tile。
- [Trunc接口](trunc_interface.md)（`related`）：GetTruncTmpBufferFactorSize 与《Trunc接口》的实质衔接是：Trunc 的 factor-size 查询要与 Trunc kernel 及 max/min 空间查询配套，才能按 maxLiveNodeCount/extraBuf 正确反推 tile。
- [GetTruncMaxMinTmpSize](get_trunc_max_min_tmp_size.md)（`same_topic`）：GetTruncMaxMinTmpSize 的核心契约是“在host侧获取Trunc接口计算所需最大和最小临时空间大小，供Tiling参数选择”；GetTruncTmpBufferFactorSize 补充“获取maxLiveNodeCount和extraBuf，用于推算Trunc接口在固定临时空间下单次最大计算元素数量”。
- [Truncf](../../../../simt_api/math_functions/float_math_functions/truncf.md)（`same_topic`）：Truncf 与《GetTruncTmpBufferFactorSize》的实质衔接是：Truncf 与 SIMD、基础、C、half/half2/bfloat16x2 Trunc 都实现向零截断；空间查询只适用于高阶 tensor 版本，不能套到标量入口。
<!-- cannbot:related:end -->
