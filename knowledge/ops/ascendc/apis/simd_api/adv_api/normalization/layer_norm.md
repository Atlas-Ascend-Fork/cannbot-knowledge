---
type: API
title: LayerNorm
description: 对shape为[B,S,H]或[A,R]的输入数据进行LayerNorm归一化，输出归一化结果及均值、方差等，通过缩放系数γ、平移系数β和防除零系数ε加速训练收敛。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/LayerNorm.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# LayerNorm

对输入数据做LayerNorm归一化，将网络层输入数据收敛以加速训练收敛。提供两种模式：对shape为[B,S,H]的输入输出归一化结果、均值和方差；对shape为[A,R]的输入输出归一化结果、均值、标准差倒数或方差。计算公式：y = γ*(x-μ)/sqrt(σ²+ε) + β，其中γ为缩放系数，β为平移系数，ε为防除零系数。模板参数T支持half/float。

提供多种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，支持不同输入/输出shape模式。Tiling参数通过LayerNorm Tiling获取。模板参数isReuseSource在float时可设为true复用srcLocal内存；isBasicBlock在满足基本块要求时可提升性能。

接口参数因模式而异，通常包含：output归一化结果；outputMean/outputVariance/outputRstd输出统计量；inputX输入；gamma/beta缩放平移系数；sharedTmpBuffer临时缓存；epsilon防除零系数；tiling切分信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：仅支持ND格式；H/R轴需满足32B对齐；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [LayerNorm 950 ACLNN 算子知识](../../../../operators/aclnn/nn/norm/layer_norm_950.md)（`related`）：｜ 计算语义 ｜ 对末尾 `normalizedShape` 轴计算 `mean`、`rstd=1/sqrt(var+eps)` 与 `y=(x-mean)*rstd*gamma+beta`；gamma/beta 可缺省。 ｜；计算公式：y = γ*(x-μ)/sqrt(σ²+ε) + β，其中γ为缩放系数，β为平移系数，ε为防除零系数。。ACLNN 算子与 Ascend C 高阶 API 共享 LayerNorm 公式，接口卡可用于理解算子 Kernel 层所实现的归一化核心。
- [LayerNorm Tiling](layer_norm_tiling.md)（`same_topic`）：“host侧Tiling接口，用于获取LayerNorm kernel计算所需的Tiling参数，分两步：通过GetLayerNormMaxMinTmpSize获取最大和最小临时空间大小；通过GetLayerNormNDTilingInfo（或GetLayerNormTmpBufferFactorSize）获取kernel侧所需tiling参数。”与“提供多种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，支持不同输入/输出shape模式。Tiling参数通过LayerNorm Tiling获取。”分别给出双端正文事实；LayerNorm Kernel 明确消费 LayerNorm Tiling，Tiling 卡生成临时空间范围与 LayerNormTiling 结构，二者定义同一归一化接口的 Host/Device 参数交接。
<!-- cannbot:related:end -->
