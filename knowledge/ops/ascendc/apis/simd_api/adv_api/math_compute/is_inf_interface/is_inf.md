---
type: API
title: IsInf
description: 按元素判断输入浮点数是否为正负无穷，输出浮点数或布尔值
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/IsInf_interface/IsInf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# IsInf

按元素判断输入浮点数是否为±INF。输出为浮点类型时，±INF位置结果为1，反之为0；输出为bool类型时，对应位置为true/false。仅Ascend 950PR/950DT支持。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetIsInfMaxMinTmpSize获取。

模板参数config为IsInfConfig类型，含isReuseSource（预留，传false）；T为目的操作数数据类型（支持bool/half/float）；U为源操作数数据类型（支持half/float）。接口参数：dst为输出操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型与src相同或为bool；src为输入操作数；sharedTmpBuffer为临时缓存；count为参与计算元素个数。

支持的输入输出数据类型组合：half-half/bool、float-float/bool。约束：不支持源操作数与目的操作数地址重叠；遵循通用地址偏移对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetIsInfMaxMinTmpSize](get_is_inf_max_min_tmp_size.md)（`related`）：IsInf 需要 sharedTmpBuffer；该 Host 查询给出可分配空间上下界，直接决定 Kernel 调用时的临时缓冲规划。
- [Isinf](../../../../simt_api/math_functions/float_math_functions/isinf.md)（`related`）：Isinf 与《IsInf》的实质衔接是：SIMT Isinf 与张量 IsInf、half/bfloat16 __hisinf 执行同一无穷判定，可按数据载体切换并核对返回语义。
- [GetIsInfTmpBufferFactorSize](get_is_inf_tmp_buffer_factor_size.md)（`same_topic`）：《GetIsInfTmpBufferFactorSize》的任务是“获取IsInf接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”。《IsInf》具体提供“按元素判断输入浮点数是否为正负无穷，输出浮点数或布尔值”，它直接用于IsInf workspace factor、上下界查询与 Kernel 调用合同。
- [IsInf接口](is_inf_interface.md)（`same_topic`）：《IsInf》明确“按元素判断输入浮点数是否为正负无穷，输出浮点数或布尔值”；它与《IsInf接口》的“按元素判断浮点数是否为±INF，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
- [__hisinf](../../../../simt_api/math_functions/bfloat16_type/bfloat16_compare_functions/_hisinf.md)（`same_topic`）：《__hisinf》处理“判断bfloat16类型浮点数是否为无穷，输入为inf或-inf时返回true。”。《IsInf》明确“按元素判断输入浮点数是否为正负无穷，输出浮点数或布尔值”，可直接用于核对half isinf 谓词与 IsInf 高阶/SIMT 实现及临时空间合同。
<!-- cannbot:related:end -->
