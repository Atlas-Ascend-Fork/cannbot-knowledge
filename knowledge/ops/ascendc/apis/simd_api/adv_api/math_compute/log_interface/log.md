---
type: API
title: Log
description: 对输入张量按元素以e、2或10为底进行对数运算，支持half和float数据类型。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Log_interface/Log.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Log

按元素做对数运算，提供以e为底（Log）、以2为底（Log2）、以10为底（Log10）三种接口。模板参数T支持half/float。

Log（以e为底）和Log10仅支持接口框架申请临时空间方式，每种区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。Log2额外支持通过sharedTmpBuffer传入临时空间。临时空间大小通过GetLogMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer（仅Log2）为临时缓存；calCount为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetLogMaxMinTmpSize](get_log_max_min_tmp_size.md)（`related`）：host侧Tiling接口，用于获取Log/Log2/Log10接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；Log（以e为底）和Log10仅支持接口框架申请临时空间方式，每种区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。Log2额外支持通过sharedTmpBuffer传入临时空间。临时空间大小通过GetLogMaxMinTmpSize获取。。Log 计算接口明确以 GetLogMaxMinTmpSize 规划 shared 临时空间，形成 host 预算到 kernel 调用的直接链。
- [GetLogTmpBufferFactorSize](get_log_tmp_buffer_factor_size.md)（`related`）：获取Log/Log2/Log10接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。；Log（以e为底）和Log10仅支持接口框架申请临时空间方式，每种区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。Log2额外支持通过sharedTmpBuffer传入临时空间。临时空间大小通过GetLogMaxMinTmpSize获取。。Factor 接口在固定临时空间下反推 Log 家族单次处理量，Log 卡说明唯一显式 sharedTmpBuffer 路径在 Log2，二者共同支撑分块预算。
- [Log2](../../../basic_api/reg_vector_compute/basic_arithmetic/log2.md)（`same_topic`）：根据mask对源操作数逐元素求以2为底的对数，将结果写入目的操作数；按元素做对数运算，提供以e为底（Log）、以2为底（Log2）、以10为底（Log10）三种接口。前者是 register vector 的 Log2，后者包含高阶 API 的 Log2，二者实现同一逐元素以 2 为底对数。
<!-- cannbot:related:end -->
