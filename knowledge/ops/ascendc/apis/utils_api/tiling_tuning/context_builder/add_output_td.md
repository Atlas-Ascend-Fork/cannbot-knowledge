---
type: API
title: AddOutputTd
description: 为算子增加输入Tensor的描述。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/AddOutputTd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AddOutputTd

为算子增加输出 Tensor 的描述信息。函数签名为 ContextBuilder& AddOutputTd(int32_t index, ge::DataType dtype, ge::Format originFormat, ge::Format storageFormat, gert::StorageShape storageShape)。
参数 index 为算子输出索引（从 0 开始）；dtype 为输出数据类型；originFormat 为原始格式；storageFormat 为运行时格式；storageShape 为输出 Shape。
返回当前 ContextBuilder 对象，支持链式调用。
约束：调用 AddOutputTd 前需要先调用 NodeIoNum 与 IrInstanceNum 接口设置算子输入输出个数与实例化个数。
典型用法：builder.NodeIoNum(1,1).IrInstanceNum({1}).AddOutputTd(0, ge::DT_FLOAT16, ge::FORMAT_ND, ge::FORMAT_ND, output_shape)。
