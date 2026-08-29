---
type: API
title: GetCosMaxMinTmpSize
description: 在host侧获取Cos接口预留临时空间的最大和最小值，用于Tiling参数选择
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Cos_interface/GetCosMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetCosMaxMinTmpSize

host侧Tiling接口，用于获取Cos接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

提供两种重载：一种不带config参数（使用默认CosConfig），另一种带config参数（须与Cos Kernel接口模板参数config保持一致）。函数原型：void GetCosMaxMinTmpSize([const CosConfig& config,] const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Cos接口保持一致，仅float支持开启，half不支持；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [GetCosTmpBufferFactorSize](get_cos_tmp_buffer_factor_size.md)（`related`）：“推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。”；“在minValue到maxValue范围内，临时空间越大性能越好。约束：无。”。factor 接口用于从现有 buffer 反推切片，max/min 接口则给出可申请字节范围，两者共同闭合 Cos tiling 预算。
- [Cos](cos.md)（`same_topic`）：“提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetCosMaxMinTmpSize获取。”与“host侧Tiling接口，用于获取Cos接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”分别给出双端正文事实；Cos Kernel 明确由 GetCosMaxMinTmpSize 确定临时空间，Host Tiling 卡输出该范围，二者是同一余弦高阶 API 的空间规划与计算合同。
<!-- cannbot:related:end -->
