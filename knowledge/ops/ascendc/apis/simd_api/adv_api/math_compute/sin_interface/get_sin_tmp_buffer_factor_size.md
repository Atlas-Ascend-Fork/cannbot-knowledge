---
type: API
title: GetSinTmpBufferFactorSize
description: 获取maxLiveNodeCount和extraBuf，用于推算Sin接口在固定临时空间下单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Sin_interface/GetSinTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetSinTmpBufferFactorSize

获取Sin接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

提供两种重载：一种不带config参数（使用默认SinConfig），另一种带config参数（须与Sin Kernel接口模板参数config保持一致）。函数原型：void GetSinTmpBufferFactorSize([const SinConfig& config,] const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [GetSinMaxMinTmpSize](get_sin_max_min_tmp_size.md)（`related`）：host侧Tiling接口，用于获取Sin接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧；推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。前者给出 Sin 临时空间的合法选择区间，后者把实际可用空间换算为单次处理元素数，属于同一 Tiling 计算链。
- [Sin](sin.md)（`related`）：GetSinTmpBufferFactorSize 给出“推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize”；Sin 页说明“提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。”，前者正用于为后者带 calCount 的显式缓冲重载推导单次计算量。
<!-- cannbot:related:end -->
