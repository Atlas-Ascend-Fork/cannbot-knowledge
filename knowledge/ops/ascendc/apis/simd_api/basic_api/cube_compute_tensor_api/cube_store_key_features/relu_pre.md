---
type: API
title: 随路Relu
description: enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_store_key_features/relu_pre.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 随路Relu

enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。

enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。 L0C Buffer到Unified Buffer搬运同样通过CopyL0C2UBTrait::enableRelu控制：

本接口属于 Cube 矩阵计算接口。

约束：enableRelu为编译期trait配置，默认不使能。；量化和Relu参数不能为inf、nan或非规格化数。；当前Tensor API不支持随路PRelu。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [随路ReLU](../../cube_compute/cube_store_key_features/accompanying_relu.md)（`same_topic`）：enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活；**DataCopyCO12DstParams结构体参数**定义中reluPre可设置为1开启Normal ReLU。两端描述矩阵结果搬出阶段开启 Normal ReLU 的同一能力，只是分别通过 Tensor trait 与基础 API 参数配置。
<!-- cannbot:related:end -->
