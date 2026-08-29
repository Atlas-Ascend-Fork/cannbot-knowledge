---
type: API
title: GetDataObj
description: 将数据指针置于GlobalTensor中并返回该GlobalTensor。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorDesc/GetDataObj.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---


# GetDataObj

将数据指针置于 GlobalTensor 中并返回该 GlobalTensor。函数签名为 GlobalTensor<T> GetDataObj()，无入参。
返回值为已设置数据指针的 GlobalTensor 对象，可用于后续搬运或计算。
该接口属于 TensorDesc 辅助数据结构基础 API，用于在 TensorDesc 与 GlobalTensor 之间传递数据指针信息。
支持 Atlas A2 与 Atlas A3 系列产品以及 Atlas 推理系列产品 AI Core 与 Vector Core，Ascend 950PR/950DT、Atlas 200I/500 A2 推理产品与 Atlas 训练系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [GetDataPtr](get_data_ptr.md)（`related`）：获取储存Tensor数据地址。；将数据指针置于 GlobalTensor 中并返回该 GlobalTensor。；两接口都在 TensorDesc 与底层 Tensor 数据之间建立访问入口；前者返回原始地址，后者把相同数据指针封装成后续搬运或计算可消费的 GlobalTensor。
<!-- cannbot:related:end -->
