---
type: API
title: Tiling调测
description: Tiling调测接口索引。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/Tiling_tuning.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Tiling调测

提供 Tiling 函数的离线调测能力，包含 OpTilingRegistry 和 ContextBuilder 两个类。OpTilingRegistry 用于加载 Tiling 实现的动态库并获取算子的 Tiling 函数指针，ContextBuilder 用于手动构造 TilingContext 或 KernelContext 以验证 Tiling 函数与 TilingParse 函数。
两者通常配合使用：ContextBuilder 构造输入参数，OpTilingRegistry 获取 Tiling 函数指针后调用执行。需包含头文件 tiling/context/context_builder.h 并链接 libtiling_api.a。
本入口包含 OpTilingRegistry 和 ContextBuilder 的成员函数导航。

<!-- cannbot:related:start -->
## 相关

- [561002：TilingParse 未生效，CompileInfo 为空](../../../runbooks/compilation/561002_tilingparse_compileinfo.md)（`exemplifies`）：该 runbook 展示离线/运行链中 TilingParse 未生效导致 CompileInfo 为空和 561002，可作为 ContextBuilder 输入完整性的失败信号。
- [BuildTilingContext](context_builder/build_tiling_context.md)（`related`）：BuildTilingContext 与《Tiling调测》的实质衔接是：BuildTilingContext 由 ContextBuilder 的算子名、属性、输入输出和平台信息构造 KernelRunContextHolder；调测页说明如何执行与检查生成的 tiling context。
- [ContextBuilder构造函数](context_builder/context_builder_constructor.md)（`related`）：ContextBuilder构造函数 与《Tiling调测》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [PlatformInfo](context_builder/platform_info.md)（`related`）：《PlatformInfo》说明将指向fe::PlatFormInfos的指针传入TilingContext。；《Tiling调测》说明Tiling调测接口索引。。二者在PlatformInfo向ContextBuilder注入fe::PlatFormInfos且只允许BuildTilingContext路径；AddPlatformInfo与Tiling调测流程给出构造和消费闭环上存在可执行的直接衔接。
- [Utils API简介](context_builder/intro.md)（`related`）：ContextBuilder 负责构造 TilingContext/KernelContext，与 Registry 组合形成完整调测链。
- [Utils API简介](op_tiling_registry/intro.md)（`related`）：Tiling 调测流程实际组合 OpTilingRegistry 加载动态库、获取函数指针和 ContextBuilder 输入，是本简介的执行落地。
- [CompileInfo](context_builder/compile_info.md)（`same_topic`）：CompileInfo 与《Tiling调测》的实质衔接是：CompileInfo 只能在 BuildTilingContext 链中注入；ContextBuilder、Outputs 回退、TilingDebug 及两张空 CompileInfo 故障直接验证上下文排序约束。
<!-- cannbot:related:end -->
