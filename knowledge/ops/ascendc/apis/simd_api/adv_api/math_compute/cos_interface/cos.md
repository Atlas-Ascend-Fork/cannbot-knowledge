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

- [Sin](../sin_interface/sin.md)（`related`）：Sin 与《Cos》的实质衔接是：这些卡覆盖 Sin 的高阶入口、临时空间计算和与 Cos 成对计算的调用方式；缓存案例与空队列案例都直接执行 sin/cos 并给出搬运或队列生命周期约束。
- [SinCos](../sin_cos_interface/sin_cos.md)（`related`）：当同一输入同时需要正弦和余弦时 SinCos 可一次生成两路结果；它与只求 Cos 的接口形成具体选型边界。
- [Tan](../tan_interface/tan.md)（`related`）：自写 tan=sin/cos 时还需处理 cos 近零和误差放大；标准 Tan 是独立基线。
- [Cos接口](cos_interface.md)（`same_topic`）：Cos 接口组页定义算法、dtype、地址与临时空间边界；Cos 卡给出四种重载以及 POLYNOMIAL_APPROXIMATION/RADIAN_REDUCTION 的具体调用契约。
- [GetCosMaxMinTmpSize](get_cos_max_min_tmp_size.md)（`same_topic`）：焦点处理Cos 的 workspace 上下界查询；Cos正文界定“按元素做余弦运算，支持多项式逼近和周期约减两种算法配置”。候选是 Cos 计算本体、接口页和 factor 查询，三者共同确定同一个 workspace 契约。
- [GetCosTmpBufferFactorSize](get_cos_tmp_buffer_factor_size.md)（`same_topic`）：GetCosTmpBufferFactorSize 给出 Cos 临时空间的固定因子计算方式，是另一条合法的 Host 侧 sizing 契约。
- [Tan接口](../tan_interface/tan_interface.md)（`same_topic`）：Tan接口 与《Cos》的实质衔接是：Tan 接口由 Tan 和两种临时空间查询组成；Atan 是反函数，Sin/Cos 卡解释 tan=sin/cos 的输入值域与验证关系。
<!-- cannbot:related:end -->
