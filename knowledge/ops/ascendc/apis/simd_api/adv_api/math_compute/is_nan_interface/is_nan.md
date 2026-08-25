---
type: API
title: IsNan
description: 按元素判断输入浮点数是否为nan，输出浮点数或布尔值
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/IsNan_interface/IsNan.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# IsNan

按元素判断输入浮点数是否为nan。输出为浮点类型时，nan位置结果为1，反之为0；输出为bool类型时，对应位置为true/false。仅Ascend 950PR/950DT支持。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetIsNanMaxMinTmpSize获取。

模板参数config为IsNanConfig类型，含isReuseSource（预留，传false）；T为目的操作数数据类型（支持bool/half/float）；U为源操作数数据类型（支持half/float）。接口参数：dst为输出操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型与src相同或为bool；src为输入操作数；sharedTmpBuffer为临时缓存；count为参与计算元素个数。

支持的输入输出数据类型组合：half-half/bool、float-float/bool。约束：不支持源操作数与目的操作数地址重叠；遵循通用地址偏移对齐约束。

<!-- cannbot:related:start -->
## 相关

- [累计极值 NaN 语义须用 self-NE 合成选择掩码](../../../../../runbooks/precision/ordered_compare_alone_cannot_propagate_nan_prefix_state.md)（`exemplifies`）：累计极值扫描需要显式识别 current/running NaN 后再合成 Select 掩码；IsNan 提供的逐元素布尔结果正是该诊断与修复链的必要信号。
- [GetIsNanTmpBufferFactorSize](get_is_nan_tmp_buffer_factor_size.md)（`related`）：该 factor 查询用于计算 IsNan Kernel 所需的 sharedTmpBuffer，直接服务于 IsNan 调用的工作空间规划。
- [Isnan](../../../../simt_api/math_functions/float_math_functions/isnan.md)（`related`）：SIMT Isnan 对单线程 float 标量判 NaN，高阶 IsNan 对 LocalTensor 批量判 NaN，可按执行模型选型。
- [GetIsNanMaxMinTmpSize](get_is_nan_max_min_tmp_size.md)（`same_topic`）：《GetIsNanMaxMinTmpSize》处理“在host侧获取IsNan接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”。《IsNan》明确提供“按元素判断输入浮点数是否为nan，输出浮点数或布尔值”，其参数、调用或验证步骤直接接入IsNan 的临时空间计算、Kernel 调用和 SIMT 对应实现。
- [IsNan接口](is_nan_interface.md)（`same_topic`）：《IsNan接口》处理“按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。”。《IsNan》提供“按元素判断输入浮点数是否为nan，输出浮点数或布尔值”，其具体合同或探针直接接入IsNan 的 Kernel/Tiling 合同、跨 dtype 谓词与 Cast 保留 NaN 的前置条件。
<!-- cannbot:related:end -->
