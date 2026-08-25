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

- [反量化 561103 实为 CheckBroadcastShape 过严](../../../../runbooks/compilation/561103_checkbroadcastshape.md)（`exemplifies`）：Dequantize 与《反量化 561103 实为 CheckBroadcastShape 过严》的实质衔接是：Dequantize 的 workspace 查询、scale/offset 设置、替代反量化入口及量化逆过程共同约束数据类型恢复；所选故障卡直接验证 scale 与广播边界。
- [矩阵乘输出的量化/反量化](../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_output_quant_dequant.md)（`explains`）：Dequantize 与《矩阵乘输出的量化/反量化》的实质衔接是：Dequantize 的 workspace 查询、scale/offset 设置、替代反量化入口及量化逆过程共同约束数据类型恢复；所选故障卡直接验证 scale 与广播边界。
- [AscendDequant](ascend_dequant.md)（`related`）：AscendDequant 与《Dequantize》的实质衔接是：AscendDequant 的两个 Host 查询共同确定 sharedTmpBuffer；Dequantize 是正文明确给出的替代入口，并改变了反量化策略与 workspace 契约。
- [CastDequant](../../basic_api/memory_vector_compute/composite_compute/cast_dequant.md)（`related`）：Dequantize 与《CastDequant》的实质衔接是：Dequantize 的 workspace 查询、scale/offset 设置、替代反量化入口及量化逆过程共同约束数据类型恢复；所选故障卡直接验证 scale 与广播边界。
- [Quantize](quantize.md)（`related`）：Dequantize 是将低精度结果恢复为高精度的逆向能力，常与 Quantize 构成压缩与恢复链。
- [SetDequantType](../cube_compute/matmul_tiling/set_dequant_type.md)（`related`）：Dequantize 与《SetDequantType》的实质衔接是：Dequantize 的 workspace 查询、scale/offset 设置、替代反量化入口及量化逆过程共同约束数据类型恢复；所选故障卡直接验证 scale 与广播边界。
- [GetDequantizeMaxMinTmpSize](get_dequantize_max_min_tmp_size.md)（`same_topic`）：GetDequantizeMaxMinTmpSize 与《Dequantize》的实质衔接是：GetDequantizeMaxMinTmpSize 与 factor 查询共同选择 kernel 临时空间，Dequantize/CastDequant 是消费端，Quantize 是逆过程，SetDequantType 决定输出模式。
- [GetDequantizeTmpBufferFactorSize](get_dequantize_tmp_buffer_factor_size.md)（`same_topic`）：Dequantize 与《GetDequantizeTmpBufferFactorSize》的实质衔接是：Dequantize 的 workspace 查询、scale/offset 设置、替代反量化入口及量化逆过程共同约束数据类型恢复；所选故障卡直接验证 scale 与广播边界。
<!-- cannbot:related:end -->
