---
type: API
title: Dequantize
description: 按元素做反量化计算，将int32_t数据类型反量化为half/float等数据类型，支持PER_TENSOR、PER_CHANNEL、PER_TOKEN、PER_GROUP四种反量化策略，最多支持二维输入。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.quantization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/quantization/Dequantize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# Dequantize

按元素做反量化计算（如int32_t反量化为half/float），将高精度整数类型转换为浮点类型。最多支持二维输入。推荐使用本接口替代AscendDequant。仅Ascend 950PR/950DT支持。

支持四种反量化策略：PER_TENSOR（scale为标量）、PER_CHANNEL（scale shape为[1,n]）、PER_TOKEN（scale shape为[m,1]）、PER_GROUP（k方向每groupSize个元素共享一组scale）。计算公式：dst = src * scale + offset（offset可选）。

提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。临时空间大小通过GetDequantizeMaxMinTmpSize获取。模板参数包含DstT目的类型、SrcT源类型、ScaleT/OffsetT系数类型。接口参数包含dstTensor输出、srcTensor输入、scale/offset反量化系数、sharedTmpBuffer临时缓存、params参数信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：最多支持二维输入；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetDequantizeMaxMinTmpSize](get_dequantize_max_min_tmp_size.md)（`related`）：“提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。临时空间大小通过GetDequantizeMaxMinTmpSize获取。”在 Kernel API 中指定 sizing 依赖；“host侧Tiling接口，用于获取Dequantize接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”给出 Host 到 Kernel 的参数交接。
- [GetDequantizeTmpBufferFactorSize](get_dequantize_tmp_buffer_factor_size.md)（`related`）：获取Dequantize接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；按元素做反量化计算（如int32_t反量化为half/float），将高精度整数类型转换为浮点类型。。前者用 maxLiveNodeCount 与 extraBuf 反推 Dequantize 单次可处理规模，后者给出被规划的反量化核心计算，二者可用于固定 UB 预算下确定一次 Dequantize 调用的数据量。
- [AscendDequant](ascend_dequant.md)（`same_topic`）：“按元素做反量化计算（如int32_t反量化为half/float），将整数类型转换为浮点类型。最多支持二维输入。推荐使用Dequantize替代本接口。支持950PR/950DT、A3、A2训练/推理、推理AI Core、Kirin X90/9030。”与“按元素做反量化计算（如int32_t反量化为half/float），将高精度整数类型转换为浮点类型。最多支持二维输入。推荐使用本接口替代AscendDequant。仅Ascend 950PR/950DT支持。”是双方正文中的具体合同。旧接口与替代接口双向声明迁移关系，核心都是 int32 到浮点的逐元素反量化；互读能核对替代时的 scale 策略和平台收缩。
<!-- cannbot:related:end -->
