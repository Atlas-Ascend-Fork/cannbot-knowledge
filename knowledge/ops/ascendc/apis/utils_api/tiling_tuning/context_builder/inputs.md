---
type: API
title: Inputs（Utils API）
description: 将void\ 指针的vector设置为KernelContext的inputs
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/Inputs.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Inputs

将 void* 指针的 vector 设置为 KernelContext 的 inputs。函数签名为 ContextBuilder& Inputs(std::vector<void*> inputs)。
参数 inputs 为保存输入的 void* 指针 vector，每个元素对应一个输入的指针。
返回当前 ContextBuilder 对象，支持链式调用。
无特殊约束。
典型用法：auto contextBuilder = context_ascendc::ContextBuilder().Inputs({nullptr, reinterpret_cast<void*>(&platformInfo)})，将平台信息指针等作为输入设置到 KernelContext 中。
