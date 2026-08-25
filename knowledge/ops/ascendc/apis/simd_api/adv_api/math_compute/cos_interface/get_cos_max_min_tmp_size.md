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

- [Cos](cos.md)（`same_topic`）：焦点处理Cos 的 workspace 上下界查询；Cos正文界定“按元素做余弦运算，支持多项式逼近和周期约减两种算法配置”。候选是 Cos 计算本体、接口页和 factor 查询，三者共同确定同一个 workspace 契约。
- [Cos接口](cos_interface.md)（`same_topic`）：焦点处理Cos 的 workspace 上下界查询；Cos接口正文界定“提供Cos余弦计算接口及其Tiling临时空间大小查询接口，包含Cos、GetCosMaxMinTmpSize等”。候选是 Cos 计算本体、接口页和 factor 查询，三者共同确定同一个 workspace 契约。
- [GetCosTmpBufferFactorSize](get_cos_tmp_buffer_factor_size.md)（`same_topic`）：焦点处理Cos 的 workspace 上下界查询；GetCosTmpBufferFactorSize正文界定“获取Cos接口的maxLiveNodeCount和extraBuf，用于推算固定空间下单次最大计算元素数”。候选是 Cos 计算本体、接口页和 factor 查询，三者共同确定同一个 workspace 契约。
<!-- cannbot:related:end -->
