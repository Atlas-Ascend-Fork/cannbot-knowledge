---
type: API
title: Cos
description: 按元素做余弦运算，支持多项式逼近和周期约减两种算法配置
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Cos_interface/Cos.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Cos

按元素做三角函数余弦运算，基于泰勒展开式实现。模板参数T支持half/float。

提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetCosMaxMinTmpSize获取。

模板参数isReuseSource仅在float时生效，true表示允许复用srcTensor内存空间；config为CosConfig类型，其中algo指定算法：POLYNOMIAL_APPROXIMATION（默认，多项式逼近，输入值域[-65504.0, 65504.0]）或RADIAN_REDUCTION（周期约减，支持输入全值域）。接口参数：dstTensor输出、srcTensor输入（TPosition为VECIN/VECCALC/VECOUT，类型需一致）、sharedTmpBuffer临时缓存、calCount参与计算元素个数。

约束：使用POLYNOMIAL_APPROXIMATION算法时，Ascend 950PR/950DT、A3、A2训练/推理、推理AI Core产品的输入源数据值域必须在[-65504.0, 65504.0]范围内；不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetCosTmpBufferFactorSize](get_cos_tmp_buffer_factor_size.md)（`related`）：“提供两种重载：一种不带config参数（使用默认CosConfig），另一种带config参数（须与Cos Kernel接口模板参数config保持一致）。”；“提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。”。Host factor 查询的 config 与 Cos kernel 模板及其 sharedTmpBuffer 路线必须一致。
- [GetCosMaxMinTmpSize](get_cos_max_min_tmp_size.md)（`same_topic`）：“提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetCosMaxMinTmpSize获取。”与“host侧Tiling接口，用于获取Cos接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”分别给出双端正文事实；Cos Kernel 明确由 GetCosMaxMinTmpSize 确定临时空间，Host Tiling 卡输出该范围，二者是同一余弦高阶 API 的空间规划与计算合同。
<!-- cannbot:related:end -->
