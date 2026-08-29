---
type: API
title: GetPowerMaxMinTmpSize
description: 在host侧获取Power接口所需的最大和最小临时空间大小，根据输入shape自动适配不同Power调用形式。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Power_interface/GetPowerMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetPowerMaxMinTmpSize

host侧Tiling接口，用于获取Power接口所需的最大和最小临时空间大小。接口内部根据srcShape1、srcShape2输入判断是Power(dstTensor, srcTensor1, srcTensor2)、Power(dstTensor, srcTensor1, scalarValue)或Power(dstTensor, scalarValue, srcTensor2)中的哪一种，返回对应临时空间大小。

函数原型：void GetPowerMaxMinTmpSize(const AscendC::TensorShape& srcShape1, const AscendC::TensorShape& srcShape2, const bool typeIsInt, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape1为srcTensor1的shape；srcShape2为srcTensor2的shape；typeIsInt为true表示输入是int32_t；typeSize为数据类型字节数（half传2）；isReuseSource与Power接口一致；maxValue输出最大临时空间大小（超出不被使用，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值）。在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [GetPowerTmpBufferFactorSize](get_power_tmp_buffer_factor_size.md)（`related`）：“currentShapeSize = (currBuff - extraBuffer) / maxLiveNodeCount / typeSize”解决固定空间下的最大计算量；“在minValue到maxValue范围内，临时空间越大性能越好。”解决固定计算量下的空间范围与性能取舍，两者是 Power tiling 的互补 sizing 路线。
- [Power（数学计算）](power.md)（`related`）：“临时空间大小通过GetPowerMaxMinTmpSize获取。”在 Power 调用契约中指定 sizing 入口；“在minValue到maxValue范围内，临时空间越大性能越好。”说明该入口返回区间内的性能取舍。
<!-- cannbot:related:end -->
