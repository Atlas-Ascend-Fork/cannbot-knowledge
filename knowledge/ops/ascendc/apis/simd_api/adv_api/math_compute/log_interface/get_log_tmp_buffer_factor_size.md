---
type: API
title: GetLogTmpBufferFactorSize
description: 获取Log/Log2/Log10接口所需的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Log_interface/GetLogTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetLogTmpBufferFactorSize

获取Log/Log2/Log10接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

提供三个重载：GetLogTmpBufferFactorSize、GetLog2TmpBufferFactorSize、GetLog10TmpBufferFactorSize，函数原型均为：void Get{Log|Log2|Log10}TmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当前Log接口（含Log2/Log10）不需要extraBuf；maxLiveNodeCount当前仅Log2接口src类型为half时需要；当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [GetLogMaxMinTmpSize](get_log_max_min_tmp_size.md)（`related`）：host侧Tiling接口，用于获取Log/Log2/Log10接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；获取Log/Log2/Log10接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。。前者从 shape 求临时空间上下界，后者从已定临时空间反推单次元素量，二者闭合 Log tiling 的正反预算。
- [Log](log.md)（`related`）：获取Log/Log2/Log10接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。；Log（以e为底）和Log10仅支持接口框架申请临时空间方式，每种区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。Log2额外支持通过sharedTmpBuffer传入临时空间。临时空间大小通过GetLogMaxMinTmpSize获取。。Factor 接口在固定临时空间下反推 Log 家族单次处理量，Log 卡说明唯一显式 sharedTmpBuffer 路径在 Log2，二者共同支撑分块预算。
<!-- cannbot:related:end -->
