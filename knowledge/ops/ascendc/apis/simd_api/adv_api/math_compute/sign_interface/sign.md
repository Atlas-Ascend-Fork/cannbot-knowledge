---
type: API
title: Sign
description: 按元素返回输入数据的符号，零返回0，正数返回1，负数返回-1。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Sign_interface/Sign.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# Sign

按元素返回输入数据的符号：0返回0，正数返回1，负数返回-1。模板参数T支持的数据类型因产品型号而异。

提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetSignMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可。接口参数：dstTensor为输出操作数，TPosition支持VECIN/VECCALC/VECOUT；srcTensor为输入操作数，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。950PR/950DT支持half/float/int64_t；A3/A2训练推理、推理AI Core、Kirin X90/9030支持half/float。

<!-- cannbot:related:start -->
## 相关

- [GetSignMaxMinTmpSize](get_sign_max_min_tmp_size.md)（`same_topic`）：临时空间大小通过GetSignMaxMinTmpSize获取；实际预留不能小于该值。Sign 的 sharedTmpBuffer 重载明确依赖 GetSignMaxMinTmpSize，查询接口给出 min/max 和性能取舍，直接决定 kernel 侧临时空间的合法容量。
- [GetSignTmpBufferFactorSize](get_sign_tmp_buffer_factor_size.md)（`same_topic`）：获取Sign接口的maxLiveNodeCount和extraBuf；临时空间大小通过GetSignMaxMinTmpSize获取。因子查询给出在固定临时空间下反推 Sign 单次元素数的公式，而 Sign 的 sharedTmpBuffer 路径需要先确定临时空间容量；两接口共同完成容量到计算规模的配置。
<!-- cannbot:related:end -->
