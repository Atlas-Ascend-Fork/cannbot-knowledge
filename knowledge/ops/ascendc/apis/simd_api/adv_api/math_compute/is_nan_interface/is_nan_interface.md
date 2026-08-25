---
type: API
title: IsNan接口
description: 按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/IsNan_interface/IsNan_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# IsNan接口

按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。

按元素判断输入的浮点数是否为nan，输出结果为浮点数或布尔值。当输出为浮点类型时，对于nan的输入数据，对应位置的结果为浮点类型的1，反之为0；当输出为bool类型时，对于nan的输入数据，对应位置的结果为true，反之为false。计算公式如下： - 当输出为浮点类型时： - 当输出为bool类型时：

本接口组包含 IsNan。

本接口属于高阶数学计算接口。

支持的数据类型为 bool、half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：不支持源操作数与目的操作数地址重叠。；操作数地址偏移对齐要求请参见通用说明和约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Cast SatMode::SAT 饱和致 fp16 NaN/Inf 丢失](../../../../../runbooks/precision/cast_satmode_sat_fp16_nan_inf.md)（`exemplifies`）：《IsNan接口》处理“按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。”。《Cast SatMode::SAT 饱和致 fp16 NaN/Inf 丢失》提供“dav-3510 上高层 AscendC::Cast 与底层 Reg::Cast 对 b16↔fp32 一律硬编码 SatMode::SAT，fp16 NaN/Inf 在第一次 b16→fp32 Cast 即被饱和为 65504，castTrait 调参（NO_SAT/默认/参考 castTraitB16ToB32）与 PostElewise Compare+Select 均无法恢复 NaN/Inf，禁止作为 NaN/Inf 传播配方。”，其具体合同或探针直接接入IsNan 的 Kernel/Tiling 合同、跨 dtype 谓词与 Cast 保留 NaN 的前置条件。
- [__hisnan](../../../../simt_api/math_functions/bfloat16_type/bfloat16_compare_functions/_hisnan.md)（`related`）：《IsNan接口》处理“按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。”。《__hisnan》提供“判断bfloat16类型浮点数是否为nan，输入为nan时返回true。”，其具体合同或探针直接接入IsNan 的 Kernel/Tiling 合同、跨 dtype 谓词与 Cast 保留 NaN 的前置条件。
- [__hisnan](../../../../simt_api/math_functions/half_type/half_compare_functions/_hisnan.md)（`related`）：《IsNan接口》处理“按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。”。《__hisnan》提供“判断浮点数是否为nan。”，其具体合同或探针直接接入IsNan 的 Kernel/Tiling 合同、跨 dtype 谓词与 Cast 保留 NaN 的前置条件。
- [__isnanx2](../../../../simt_api/math_functions/bfloat16_type/bfloat16x2_compare_functions/_isnanx2.md)（`related`）：《IsNan接口》处理“按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。”。《__isnanx2》提供“判断bfloat16x2_t类型数据的两个分量是否为nan。”，其具体合同或探针直接接入IsNan 的 Kernel/Tiling 合同、跨 dtype 谓词与 Cast 保留 NaN 的前置条件。
- [__isnanx2](../../../../simt_api/math_functions/half_type/half2_compare_functions/_isnanx2.md)（`related`）：《IsNan接口》处理“按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。”。《__isnanx2》提供“判断half2类型数据的两个分量是否为nan。”，其具体合同或探针直接接入IsNan 的 Kernel/Tiling 合同、跨 dtype 谓词与 Cast 保留 NaN 的前置条件。
- [GetIsNanMaxMinTmpSize](get_is_nan_max_min_tmp_size.md)（`same_topic`）：《IsNan接口》处理“按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。”。《GetIsNanMaxMinTmpSize》提供“在host侧获取IsNan接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”，其具体合同或探针直接接入IsNan 的 Kernel/Tiling 合同、跨 dtype 谓词与 Cast 保留 NaN 的前置条件。
- [GetIsNanTmpBufferFactorSize](get_is_nan_tmp_buffer_factor_size.md)（`same_topic`）：《IsNan接口》处理“按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。”。《GetIsNanTmpBufferFactorSize》提供“获取IsNan接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”，其具体合同或探针直接接入IsNan 的 Kernel/Tiling 合同、跨 dtype 谓词与 Cast 保留 NaN 的前置条件。
- [IsNan](is_nan.md)（`same_topic`）：《IsNan接口》处理“按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。”。《IsNan》提供“按元素判断输入浮点数是否为nan，输出浮点数或布尔值”，其具体合同或探针直接接入IsNan 的 Kernel/Tiling 合同、跨 dtype 谓词与 Cast 保留 NaN 的前置条件。
- [Isnan](../../../../simt_api/math_functions/float_math_functions/isnan.md)（`same_topic`）：《IsNan接口》处理“按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。”。《Isnan》提供“判断浮点数是否为nan。”，其具体合同或探针直接接入IsNan 的 Kernel/Tiling 合同、跨 dtype 谓词与 Cast 保留 NaN 的前置条件。
<!-- cannbot:related:end -->
