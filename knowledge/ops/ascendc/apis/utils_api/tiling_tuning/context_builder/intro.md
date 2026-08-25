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

<!-- cannbot:related:start -->
## 相关

- [BuildKernelRunContext](build_kernel_run_context.md)（`related`）：ContextBuilder 也可构造 KernelRunContext 供 TilingParse 验证，与 TilingContext 分别服务两类回调。
- [BuildTilingContext](build_tiling_context.md)（`related`）：简介说明 ContextBuilder 用于手工构造 TilingContext，BuildTilingContext 是将 inputs、attrs、platform 等配置固化的终点。
- [PlatformInfo](platform_info.md)（`related`）：《PlatformInfo》说明将指向fe::PlatFormInfos的指针传入TilingContext。；《Utils API简介》说明ContextBuilder类提供一系列的API接口，支持手动构造TilingContext类来验证Tiling函数以及KernelContext类用于TilingParse函数的验证。。二者在PlatformInfo向ContextBuilder注入fe::PlatFormInfos且只允许BuildTilingContext路径；AddPlatformInfo与Tiling调测流程给出构造和消费闭环上存在可执行的直接衔接。
- [Tiling调测](../tiling_tuning.md)（`related`）：ContextBuilder 负责构造 TilingContext/KernelContext，与 Registry 组合形成完整调测链。
- [Workspace（Utils API）](workspace.md)（`same_topic`）：ContextBuilder 介绍说明该类用于手工构造 TilingContext/KernelContext 做 Tiling 单测，Workspace 是其中的输出指针注入项。
<!-- cannbot:related:end -->
