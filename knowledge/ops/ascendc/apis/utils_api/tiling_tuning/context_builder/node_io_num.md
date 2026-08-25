---
type: API
title: NodeIoNum
description: 声明算子定义的输入与输出个数
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/NodeIoNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# NodeIoNum

声明算子定义的输入与输出个数。函数签名为 ContextBuilder& NodeIoNum(size_t inputNum, size_t outputNum)。
参数 inputNum 为算子 IR 原型定义中的输入个数，outputNum 为输出个数。
返回当前 ContextBuilder 对象，支持链式调用。
约束：必须配合 IrInstanceNum 一同使用，先通过 NodeIoNum 设置输入输出个数，再通过 IrInstanceNum 设置每种输入的实例化个数。
典型用法：auto builder = ContextBuilder().NodeIoNum(5, 3)，表示该算子有 5 个输入和 3 个输出。
