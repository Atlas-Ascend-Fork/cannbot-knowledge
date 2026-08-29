---
type: API
title: AscendAntiQuant
description: 按元素做伪量化计算，将int8_t数据类型伪量化为half数据类型，支持PER_CHANNEL场景，可选开启输入转置。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.quantization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/quantization/AscendAntiQuant.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# AscendAntiQuant

按元素做伪量化计算（如int8_t伪量化为half），计算公式：dst = scale * (src + offset)。支持PER_CHANNEL（按通道量化）和PER_GROUP（按组量化）策略，支持输入转置配置。推荐使用AntiQuantize替代本接口。支持950PR/950DT、A3、A2训练/推理、推理AI Core、Kirin X90/9030。

提供多种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，支持不同量化场景（标量/矢量scale、是否转置等）。临时空间大小通过GetAscendAntiQuantMaxMinTmpSize获取。

接口参数包含dstTensor输出、srcTensor输入（shape [m,n]）、scale/offset量化系数（shape因策略而异）、sharedTmpBuffer临时缓存、params参数信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：最多支持二维输入；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetAscendAntiQuantMaxMinTmpSize](get_ascend_anti_quant_max_min_tmp_size.md)（`related`）：“host侧Tiling接口，用于获取AscendAntiQuant接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”与“临时空间大小通过GetAscendAntiQuantMaxMinTmpSize获取。”是双方正文中的具体合同。Tiling 卡提供 AscendAntiQuant workspace 上下界，计算卡明确由它取得临时空间大小，二者闭合 Host 尺寸规划和 Kernel 侧调用。
- [GetAscendAntiQuantTmpBufferFactorSize](get_ascend_anti_quant_tmp_buffer_factor_size.md)（`related`）：“推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。”；“接口参数包含dstTensor输出、srcTensor输入（shape ［m,n］）、scale/offset量化系数（shape因策略而异）、sharedTmpBuffer临时缓存、params参数信息。”。factor 接口把可用缓冲换算为 currentShapeSize，AscendAntiQuant 计算接口实际消费 sharedTmpBuffer。
- [AntiQuantize](anti_quantize.md)（`same_topic`）：“按元素做伪量化计算（如int8_t伪量化为half），计算公式：dst = scale * (src + offset)。支持PER_CHANNEL（按通道量化）和PER_GROUP（按组量化）策略，支持输入转置配置。推荐使用AntiQuantize替代本接口。支持950PR/950DT、A3、A2训练/推理、推理AI Core、Kirin X90/9030。”与“按元素做伪量化计算（如int8_t伪量化为half），将低精度数据类型转换为高精度数据类型。最多支持二维输入。推荐使用本接口替代AscendAntiQuant，因其在不同量化场景下形式更统一。仅Ascend 950PR/950DT支持。”是双方正文中的具体合同。旧接口正文明确指向 AntiQuantize，替代接口又反向声明取代 AscendAntiQuant；二者围绕同一伪量化核心合同，可用于迁移时核对策略与平台差异。
<!-- cannbot:related:end -->
