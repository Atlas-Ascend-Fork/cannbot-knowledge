---
type: API
title: IrInstanceNum
description: 基于算子的IR定义，声明实例化时每种输入的实际个数。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/IrInstanceNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# IrInstanceNum

基于算子 IR 定义，声明实例化时每种输入的实际个数。函数签名为 ContextBuilder& IrInstanceNum(std::vector<uint32_t> instanceNum)。
参数 instanceNum 为按输入 index 顺序声明的实例化个数向量，用于描述动态类型输入 Tensor 的实例数量。
返回当前 ContextBuilder 对象，支持链式调用。
约束：必须配合 NodeIoNum 一同使用，先通过 NodeIoNum 设置算子输入输出个数，再通过 IrInstanceNum 设置实例化个数。
典型用法：builder.NodeIoNum(5,3).IrInstanceNum({1, 1, 3, 1, 1})，表示 index 为 2 的动态类型输入有 3 个实例。
