---
type: API
title: TensorShape
description: AscendC::TensorShape是ge::Shape的类型别名，用于描述高阶API的Host侧Tiling接口使用的Tensor形状。
  具体使用请参考ge::Shape。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/data_structures/TensorShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# TensorShape

## 功能说明

`AscendC::TensorShape`是`ge::Shape`的类型别名，用于描述高阶API的Host侧Tiling接口使用的Tensor形状。

具体使用请参考[ge::Shape](https://gitcode.com/cann/metadef/blob/master/docs/api/ge_namespace/shape/Shape.md)。

<!-- cannbot:related:start -->
## 相关

- [GetShapeInfo](../../basic_api/data_structures/global_tensor/get_shape_info.md)（`related`）：GetShapeInfo 与《TensorShape》的实质衔接是：GetShapeInfo 只有在对应 GlobalTensor 已 SetShapeInfo 后才有效；ShapeInfo、SetGlobalBuffer 与 tensor 子视图共同约束 shape 元数据生命周期。
- [TensorDataType](tensor_data_type.md)（`related`）：TensorShape 与 TensorDataType 共同组成高阶 API Host Tiling 对输入张量的形状和类型描述契约。
<!-- cannbot:related:end -->
