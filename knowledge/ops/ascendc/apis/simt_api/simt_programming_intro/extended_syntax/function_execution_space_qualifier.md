---
type: API
title: 函数执行空间限定符
description: 函数执行空间限定符（Function Execution Space Qualifier）指示函数是在Host侧执行还是在Device侧执行，以及能被调用的空间范围。
tags: [task.lookup, topic.implementation.api_layer.simt_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMT_programming_intro/extended_syntax/function_execution_space_qualifier.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 函数执行空间限定符

函数执行空间限定符（Function Execution Space Qualifier）指示函数在 Host 侧还是 Device 侧执行，以及能被调用的空间范围。

三种限定符：__host__（Host 侧执行，只能被 Host 函数调用，无限定符时默认为 host）、__global__（Device 侧执行，核函数入口，只能被 Host 调用，返回类型必须为 void，不支持递归，调用为异步）、__aicore__（Device 侧执行，只能被 __global__ 或其他 __aicore__ 函数调用）。

调用关系：Host 可调用 __global__ 核函数；__global__ 可调用 __aicore__；__aicore__ 间可互相调用。

<!-- cannbot:related:start -->
## 相关

- [核函数调用未标__aicore__的纯算术辅助函数](../../../../runbooks/compilation/aicore_helper_requires_device_qualifier.md)（`exemplifies`）：__aicore__（Device 侧执行，只能被 __global__ 或其他 __aicore__ 函数调用）。；在 `.asc` 中，普通 `static inline` 并不会自动获得 device 调用属性。；Runbook 将限定符调用合同落到 host helper 被 device kernel 拒绝的编译故障。
<!-- cannbot:related:end -->
