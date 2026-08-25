---
type: API
title: SetShapeAddr
description: 配置用于储存shape信息的地址。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorDesc/SetShapeAddr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# SetShapeAddr

配置用于储存shape信息的地址。本接口属于 Tensor 描述符辅助接口，用于设置 TensorDesc 中存储 shape 信息的内存地址。

函数原型为 void SetShapeAddr(uint64_t* shapePtr)，参数 shapePtr 为输入参数，类型为 uint64_t 指针，指向用于储存 shape 信息的地址。

支持的硬件型号：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品 AI Core、Atlas 推理系列产品 Vector Core。返回值无，约束说明无。

<!-- cannbot:related:start -->
## 相关

- [GetDim](get_dim.md)（`related`）：SetShapeAddr 写入 TensorDesc 的 shape 存储，GetDim 随后读取该元信息形成写后验证链。
- [GetShapeInfo](../../data_structures/global_tensor/get_shape_info.md)（`related`）：GetShapeInfo 与《SetShapeAddr》的实质衔接是：GetShapeInfo 只有在对应 GlobalTensor 已 SetShapeInfo 后才有效；ShapeInfo、SetGlobalBuffer 与 tensor 子视图共同约束 shape 元数据生命周期。
- [构造和析构函数](constructor_and_destructor.md)（`related`）：默认构造得到空描述符时，SetShapeAddr 可补入 shape 地址，是另一种实际初始化路径。
- [GetShape](get_shape.md)（`same_topic`）：SetShapeAddr 绑定 shape 存储后，GetShape 读取同一 TensorDesc 元信息，可做写后校验。
<!-- cannbot:related:end -->
