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

- [Dequantize](dequantize.md)（`related`）：AscendDequant 与《Dequantize》的实质衔接是：AscendDequant 的两个 Host 查询共同确定 sharedTmpBuffer；Dequantize 是正文明确给出的替代入口，并改变了反量化策略与 workspace 契约。
- [GetAscendDequantMaxMinTmpSize](get_ascend_dequant_max_min_tmp_size.md)（`related`）：AscendDequant 是该 Host workspace 查询所服务的 Kernel 计算接口，isReuseSource 和 typeSize 必须在两侧一致。
- [GetAscendDequantTmpBufferFactorSize](get_ascend_dequant_tmp_buffer_factor_size.md)（`same_topic`）：GetAscendDequantTmpBufferFactorSize 与《AscendDequant》的实质衔接是：factor 查询与 GetAscendDequantMaxMinTmpSize 共同换算临时空间和单次元素数，AscendDequant 是结果消费方，SetDequantType 控制输出模式。
<!-- cannbot:related:end -->
