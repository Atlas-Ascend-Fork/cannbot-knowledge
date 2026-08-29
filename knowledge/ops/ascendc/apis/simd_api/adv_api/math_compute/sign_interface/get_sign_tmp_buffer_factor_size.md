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

- [GetSignMaxMinTmpSize](get_sign_max_min_tmp_size.md)（`related`）：开发者据此选择合适的Tiling参数传入kernel侧；推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize。总量接口确定 Sign 临时空间可选范围，因子接口把实际可用空间反推为单次最大元素数，二者组成 host 到 kernel 的分块 Tiling 计算。
- [Sign](sign.md)（`same_topic`）：获取Sign接口的maxLiveNodeCount和extraBuf；临时空间大小通过GetSignMaxMinTmpSize获取。因子查询给出在固定临时空间下反推 Sign 单次元素数的公式，而 Sign 的 sharedTmpBuffer 路径需要先确定临时空间容量；两接口共同完成容量到计算规模的配置。
<!-- cannbot:related:end -->
