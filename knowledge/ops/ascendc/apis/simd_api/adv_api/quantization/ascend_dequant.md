---
type: API
title: AscendDequant
description: 按元素做反量化计算，将int32_t数据类型反量化为half/float等数据类型，反量化系数可为标量或向量，最多支持二维输入。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.quantization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/quantization/AscendDequant.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# AscendDequant

按元素做反量化计算（如int32_t反量化为half/float），将整数类型转换为浮点类型。最多支持二维输入。推荐使用Dequantize替代本接口。支持950PR/950DT、A3、A2训练/推理、推理AI Core、Kirin X90/9030。

输入srcTensor shape为(m,n)，每行数据需32字节对齐，每行反量化元素个数为calCount。反量化系数deqScale可为标量或向量，向量模式下calCount需小于等于deqScale元素个数。输出dstTensor shape为(m,n_dst)，n*sizeof(dstT)不满足32B对齐时需向上补齐。

提供多种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，支持标量/矢量scale场景。临时空间大小通过GetAscendDequantMaxMinTmpSize获取。接口参数包含dstTensor输出、srcTensor输入、deqScale反量化系数、sharedTmpBuffer临时缓存、params参数信息（含m,n,calCount）。

约束：最多支持二维输入；每行数据32B对齐；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetAscendDequantMaxMinTmpSize](get_ascend_dequant_max_min_tmp_size.md)（`related`）：先用“host侧Tiling接口，用于获取AscendDequant接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”在 max/min 范围内选择空间，再遵守“提供多种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，支持标量/矢量scale场景。临时空间大小通过GetAscendDequantMaxMinTmpSize获取。”把空间交给标量或矢量 scale 重载，可直接排查临时空间和 isReuseSource 配置。
- [GetAscendDequantTmpBufferFactorSize](get_ascend_dequant_tmp_buffer_factor_size.md)（`related`）：选择“提供多种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，支持标量/矢量scale场景。临时空间大小通过GetAscendDequantMaxMinTmpSize获取。”的显式 sharedTmpBuffer 重载后，用“获取AscendDequant接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。”的 maxLiveNodeCount 与 extraBuf 反算 currentShapeSize，并处理 maxLiveNodeCount 为零的边界。
- [Dequantize](dequantize.md)（`same_topic`）：“按元素做反量化计算（如int32_t反量化为half/float），将整数类型转换为浮点类型。最多支持二维输入。推荐使用Dequantize替代本接口。支持950PR/950DT、A3、A2训练/推理、推理AI Core、Kirin X90/9030。”与“按元素做反量化计算（如int32_t反量化为half/float），将高精度整数类型转换为浮点类型。最多支持二维输入。推荐使用本接口替代AscendDequant。仅Ascend 950PR/950DT支持。”是双方正文中的具体合同。旧接口与替代接口双向声明迁移关系，核心都是 int32 到浮点的逐元素反量化；互读能核对替代时的 scale 策略和平台收缩。
<!-- cannbot:related:end -->
