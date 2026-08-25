---
type: API
title: GetIsInfMaxMinTmpSize
description: 在host侧获取IsInf接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/IsInf_interface/GetIsInfMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# GetIsInfMaxMinTmpSize

host侧Tiling接口，用于获取IsInf接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetIsInfMaxMinTmpSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：ascendcPlatform为平台信息；srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource预留，传false；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [IsInf](is_inf.md)（`related`）：IsInf 需要 sharedTmpBuffer；该 Host 查询给出可分配空间上下界，直接决定 Kernel 调用时的临时缓冲规划。
- [IsInf接口](is_inf_interface.md)（`related`）：《GetIsInfMaxMinTmpSize》明确“在host侧获取IsInf接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”；它与《IsInf接口》的“按元素判断浮点数是否为±INF，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetIsInfTmpBufferFactorSize](get_is_inf_tmp_buffer_factor_size.md)（`same_topic`）：《GetIsInfTmpBufferFactorSize》的任务是“获取IsInf接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”。《GetIsInfMaxMinTmpSize》具体提供“在host侧获取IsInf接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”，它直接用于IsInf workspace factor、上下界查询与 Kernel 调用合同。
- [__hisinf](../../../../simt_api/math_functions/bfloat16_type/bfloat16_compare_functions/_hisinf.md)（`same_topic`）：《__hisinf》处理“判断bfloat16类型浮点数是否为无穷，输入为inf或-inf时返回true。”。《GetIsInfMaxMinTmpSize》明确“在host侧获取IsInf接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”，可直接用于核对half isinf 谓词与 IsInf 高阶/SIMT 实现及临时空间合同。
<!-- cannbot:related:end -->
