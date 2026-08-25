---
type: API
title: GetSignTmpBufferFactorSize
description: 获取maxLiveNodeCount和extraBuf，用于推算Sign接口在固定临时空间下单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Sign_interface/GetSignTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetSignTmpBufferFactorSize

获取Sign接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetSignTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [GetSignMaxMinTmpSize](get_sign_max_min_tmp_size.md)（`same_topic`）：GetSignTmpBufferFactorSize：该因子接口只服务 Sign 的临时空间反推；Sign与接口页定义 kernel计算，MaxMinTmpSize给出另一种从shape正向估算的预算方式。 目标卡《GetSignMaxMinTmpSize》补充：在host侧获取Sign接口计算所需最大和最小临时空间大小，供Tiling参数选择。
- [Sign](sign.md)（`same_topic`）：GetSignTmpBufferFactorSize：该因子接口只服务 Sign 的临时空间反推；Sign与接口页定义 kernel计算，MaxMinTmpSize给出另一种从shape正向估算的预算方式。 目标卡《Sign》补充：按元素返回输入数据的符号，零返回0，正数返回1，负数返回-1。
- [Sign接口](sign_interface.md)（`same_topic`）：GetSignTmpBufferFactorSize：该因子接口只服务 Sign 的临时空间反推；Sign与接口页定义 kernel计算，MaxMinTmpSize给出另一种从shape正向估算的预算方式。 目标卡《Sign接口》补充：按元素返回输入数据的符号（正数为1、负数为-1、零为0），并提供临时空间大小获取接口。
<!-- cannbot:related:end -->
