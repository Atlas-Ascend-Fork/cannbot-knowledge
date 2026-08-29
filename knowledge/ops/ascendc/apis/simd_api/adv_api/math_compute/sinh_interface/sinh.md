---
type: API
title: Sinh
description: 按元素对输入数据做双曲正弦函数计算。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Sinh_interface/Sinh.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# Sinh

按元素做双曲正弦函数计算。模板参数T支持half/float。

提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetSinhMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetSinhMaxMinTmpSize](get_sinh_max_min_tmp_size.md)（`related`）：host侧Tiling接口，用于获取Sinh接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetSinhMaxMinTmpSize获取。；Sinh 正文明确把该 Tiling 接口作为临时空间大小来源，构成 Host 选参到 kernel 重载的直接合同。
- [GetSinhTmpBufferFactorSize](get_sinh_tmp_buffer_factor_size.md)（`related`）：“临时空间大小通过GetSinhMaxMinTmpSize获取”给出容量范围入口，“currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize”进一步把固定容量换算为单次计算元素数，二者共同完成 Tiling。
<!-- cannbot:related:end -->
