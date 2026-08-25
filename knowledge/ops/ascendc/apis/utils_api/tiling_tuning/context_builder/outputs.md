---
type: API
title: Outputs（Utils API）
description: 将void\ 指针的vector设置为KernelContext的output。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/Outputs.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Outputs

将 void* 指针的 vector 设置为 KernelContext 的 outputs。函数签名为 ContextBuilder& Outputs(std::vector<void*> outputs)。
参数 outputs 为保存输出的 void* 指针 vector，每个元素对应一个输出的指针。
返回当前 ContextBuilder 对象，支持链式调用。
无特殊约束。
典型用法：auto contextBuilder = context_ascendc::ContextBuilder().Outputs({nullptr, reinterpret_cast<void*>(&platformInfo)})，将输出指针设置到 KernelContext 中。
