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

- [AscendQuant](ascend_quant.md)（`related`）：AscendAntiQuant 与《AscendQuant》的实质衔接是：AscendAntiQuant 依赖两种空间查询，generic AntiQuant 是同任务入口，AscendQuant 是逆过程；scale 错配卡直接约束分组反量化。
- [AntiQuantize](anti_quantize.md)（`same_topic`）：AscendAntiQuant 与《AntiQuantize》的实质衔接是：AscendAntiQuant 依赖两种空间查询，generic AntiQuant 是同任务入口，AscendQuant 是逆过程；scale 错配卡直接约束分组反量化。
- [GetAscendAntiQuantMaxMinTmpSize](get_ascend_anti_quant_max_min_tmp_size.md)（`same_topic`）：GetAscendAntiQuantMaxMinTmpSize 与《AscendAntiQuant》的实质衔接是：GetAscendAntiQuantMaxMinTmpSize 与 factor 查询、AscendAntiQuant kernel 成对使用；分组 scale 错配卡直接验证该反量化任务的输入契约。
- [GetAscendAntiQuantTmpBufferFactorSize](get_ascend_anti_quant_tmp_buffer_factor_size.md)（`same_topic`）：GetAscendAntiQuantTmpBufferFactorSize 与《AscendAntiQuant》的实质衔接是：AscendAntiQuant 的 MaxMin/factor 查询共同决定临时空间和单次处理量；分组 scale 的 cyclic-repeat 故障直接验证反量化系数布局。
<!-- cannbot:related:end -->
