---
type: API
title: Utils API简介
description: ContextBuilder类提供一系列的API接口，支持手动构造TilingContext类来验证Tiling函数以及KernelContext类用于TilingParse函数的验证。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# ContextBuilder简介

ContextBuilder类提供一系列API接口，支持手动构造TilingContext类来验证Tiling函数，以及构造KernelContext类用于TilingParse函数的验证。通过链式调用Inputs、Outputs、SetOpNameType、NodeIoNum、IrInstanceNum、AddInputTd、AddOutputTd、AddAttr等方法配置上下文参数，最后调用BuildKernelRunContext或BuildTilingContext生成目标上下文对象。适用于算子开发阶段的Tiling逻辑单元测试，脱离图引擎独立验证Tiling计算结果。
