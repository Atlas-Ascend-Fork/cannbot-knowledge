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

- [GetSignMaxMinTmpSize](get_sign_max_min_tmp_size.md)（`same_topic`）：Sign 计算的 sharedTmpBuffer 由该 Host 接口按 shape 查询并写入 Tiling。
- [GetSignTmpBufferFactorSize](get_sign_tmp_buffer_factor_size.md)（`same_topic`）：GetSignTmpBufferFactorSize：该因子接口只服务 Sign 的临时空间反推；Sign与接口页定义 kernel计算，MaxMinTmpSize给出另一种从shape正向估算的预算方式。 目标卡《Sign》补充：按元素返回输入数据的符号，零返回0，正数返回1，负数返回-1。
- [Sign接口](sign_interface.md)（`same_topic`）：Sign说明按元素返回输入数据的符号，零返回0，正数返回1，负数返回-1。
<!-- cannbot:related:end -->
