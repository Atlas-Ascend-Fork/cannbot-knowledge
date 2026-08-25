---
type: API
title: IsInf接口
description: 按元素判断浮点数是否为±INF，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/IsInf_interface/IsInf_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# IsInf接口

按元素判断浮点数是否为±INF，并提供临时空间大小获取接口。

按元素判断输入的浮点数是否为±INF，输出结果为浮点数或布尔值。当输出为浮点类型时，对于±INF的输入数据，对应位置的结果为浮点类型的1，反之为0；当输出为bool类型时，对于±INF的输入数据，对应位置的结果为true，反之为false。计算公式如下： - 当输出为浮点类型时： - 当输出为bool类型时：

本接口组包含 IsInf。

本接口属于高阶数学计算接口。

支持的数据类型为 bool、half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：不支持源操作数与目的操作数地址重叠。；操作数地址偏移对齐要求请参见通用说明和约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [GetIsInfMaxMinTmpSize](get_is_inf_max_min_tmp_size.md)（`related`）：《GetIsInfMaxMinTmpSize》明确“在host侧获取IsInf接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”；它与《IsInf接口》的“按元素判断浮点数是否为±INF，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
- [Isinf](../../../../simt_api/math_functions/float_math_functions/isinf.md)（`related`）：《Isinf》明确“判断浮点数是否为无穷。”；它与《IsInf接口》的“按元素判断浮点数是否为±INF，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetIsInfTmpBufferFactorSize](get_is_inf_tmp_buffer_factor_size.md)（`same_topic`）：《GetIsInfTmpBufferFactorSize》的任务是“获取IsInf接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”。《IsInf接口》具体提供“按元素判断浮点数是否为±INF，并提供临时空间大小获取接口。”，它直接用于IsInf workspace factor、上下界查询与 Kernel 调用合同。
- [IsInf](is_inf.md)（`same_topic`）：《IsInf》明确“按元素判断输入浮点数是否为正负无穷，输出浮点数或布尔值”；它与《IsInf接口》的“按元素判断浮点数是否为±INF，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
- [__hisinf](../../../../simt_api/math_functions/bfloat16_type/bfloat16_compare_functions/_hisinf.md)（`same_topic`）：《__hisinf》处理“判断bfloat16类型浮点数是否为无穷，输入为inf或-inf时返回true。”。《IsInf接口》明确“按元素判断浮点数是否为±INF，并提供临时空间大小获取接口。”，可直接用于核对half isinf 谓词与 IsInf 高阶/SIMT 实现及临时空间合同。
<!-- cannbot:related:end -->
