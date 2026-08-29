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

- [GetIsNanMaxMinTmpSize](get_is_nan_max_min_tmp_size.md)（`related`）：host侧Tiling接口，用于获取IsNan接口所需的最大和最小临时空间大小；临时空间大小通过GetIsNanMaxMinTmpSize获取。。左卡返回 IsNan 可用临时空间范围，右卡明确由该查询结果为 sharedTmpBuffer 定容；两端直接衔接 950 Host Tiling 与按元素 NaN 判定 Kernel。
- [GetIsNanTmpBufferFactorSize](get_is_nan_tmp_buffer_factor_size.md)（`related`）：参数：ascendcPlatform为平台信息；typeSize为输入数据类型字节数（half传2）；maxLivedNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLivedNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。；提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetIsNanMaxMinTmpSize获取。。前者给出固定临时空间下 IsNan 单次处理量的反推公式，后者是实际消费 sharedTmpBuffer 的逐元素 NaN 判断接口。
<!-- cannbot:related:end -->
