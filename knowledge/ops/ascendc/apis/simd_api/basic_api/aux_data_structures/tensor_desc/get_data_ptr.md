---
type: API
title: GetDataPtr
description: 获取储存Tensor数据地址。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorDesc/GetDataPtr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# GetDataPtr

获取储存Tensor数据地址。

获取储存Tensor数据地址。

本接口属于 Tensor 数据结构操作接口。

返回值：返回储存Tensor数据地址。T数据类型。

支持的硬件型号：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core。

<!-- cannbot:related:start -->
## 相关

- [ForeachTan 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_tan_950.md)（`related`）：“xPtr=xList.GetDataPtr<float>(i); yPtr=yList.GetDataPtr<float>(i)”给出 FP32 route 从列表描述符取 GM 地址的实际调用；“获取储存Tensor数据地址。”定义 GetDataPtr 返回的数据。
- [GetDataObj](get_data_obj.md)（`related`）：获取储存Tensor数据地址。；将数据指针置于 GlobalTensor 中并返回该 GlobalTensor。；两接口都在 TensorDesc 与底层 Tensor 数据之间建立访问入口；前者返回原始地址，后者把相同数据指针封装成后续搬运或计算可消费的 GlobalTensor。
<!-- cannbot:related:end -->
