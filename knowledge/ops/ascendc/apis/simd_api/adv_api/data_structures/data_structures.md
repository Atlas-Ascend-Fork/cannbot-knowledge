---
type: API
title: 数据结构
description: 汇总高阶API在Host侧Tiling接口中使用的Ascend C公共类型，包含TensorShape、TensorDataType等数据结构定义。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/data_structures/data_structures.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 数据结构

汇总高阶API在Host侧Tiling接口中使用的Ascend C公共类型，包含TensorShape、TensorDataType等数据结构定义。

AscendC::TensorShape是ge::Shape的类型别名，用于描述高阶API的Host侧Tiling接口使用的Tensor形状。 具体使用请参考ge::Shape。

本接口组包含 TensorShape, TensorDataType。

本接口属于 Tensor 数据结构操作接口。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [TensorDataType](tensor_data_type.md)（`same_topic`）：TensorDataType 与《数据结构》的实质衔接是：TensorDataType 与 TensorShape 都是高阶 API Host Tiling 公共类型；SetAType 的 dataType 参数展示该 ge::DataType 别名如何进入矩阵类型配置。
<!-- cannbot:related:end -->
