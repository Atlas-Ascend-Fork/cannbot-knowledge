---
type: API
title: CompileInfo
description: 将指向CompileInfo的指针传入TilingContext
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/CompileInfo.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# CompileInfo

## 功能说明
将指向CompileInfo的指针传入TilingContext
## 函数原型
## 参数说明
## 返回值说明
当前ContextBuilder的对象。
## 约束说明
由于TilingContext与KernelContext、TilingParseContext内部数据排序不同，CompileInfo()只支持以调用BuildTilingContext()为前提来使用；其他场景建议用Outputs接口，否则发生未定义行为。

<!-- cannbot:related:start -->
## 相关

- [561002：TilingParse 未生效，CompileInfo 为空](../../../../runbooks/compilation/561002_tilingparse_compileinfo.md)（`exemplifies`）：CompileInfo 与《561002：TilingParse 未生效，CompileInfo 为空》的实质衔接是：CompileInfo 只能在 BuildTilingContext 链中注入；ContextBuilder、Outputs 回退、TilingDebug 及两张空 CompileInfo 故障直接验证上下文排序约束。
- [te_fusion 未调 TilingPrepare 致 GEIR FPE](../../../../runbooks/compilation/te_fusion_tilingprepare_geir_fpe.md)（`exemplifies`）：“te_fusion 未调 TilingPrepare 致 GEIR FPE”定义：GEIR 图测试全 case 返回 GE error 4294967295 并抛 Python FPE；根因是 GE te_fusion/build_single_op 编译子路径不调 TilingParse<TilingPrepare> 填 compileInfo，tiling 函数读 compileInfo=0 除零。用 fprintf 探针判别三条 run 路径的 TilingPrepare 调用语义。；“CompileInfo”定义：将指向CompileInfo的指针传入TilingContext。实质衔接：两卡都定位 TilingParse/TilingPrepare 未填 CompileInfo；ContextBuilder 的平台与 CompileInfo 注入接口用于构造可执行探针和避免除零。
- [TilingDebug](../../../../guides/programming_guide/appendix/common_operations/tiling_debug.md)（`explains`）：CompileInfo 与《TilingDebug》的实质衔接是：CompileInfo 只能在 BuildTilingContext 链中注入；ContextBuilder、Outputs 回退、TilingDebug 及两张空 CompileInfo 故障直接验证上下文排序约束。
- [AddAttr](add_attr.md)（`same_topic`）：AddAttr 与《CompileInfo》的实质衔接是：AddAttr 是 ContextBuilder 链式构造 tiling/kernel 上下文的一环；构造、I/O、算子名、平台、CompileInfo 和 Build 方法共同决定属性如何进入 KernelRunContext。
- [BuildTilingContext](build_tiling_context.md)（`same_topic`）：CompileInfo 与《BuildTilingContext》的实质衔接是：CompileInfo 只能在 BuildTilingContext 链中注入；ContextBuilder、Outputs 回退、TilingDebug 及两张空 CompileInfo 故障直接验证上下文排序约束。
- [ContextBuilder](context_builder.md)（`same_topic`）：CompileInfo 与《ContextBuilder》的实质衔接是：CompileInfo 只能在 BuildTilingContext 链中注入；ContextBuilder、Outputs 回退、TilingDebug 及两张空 CompileInfo 故障直接验证上下文排序约束。
- [ContextBuilder构造函数](context_builder_constructor.md)（`same_topic`）：CompileInfo 与《ContextBuilder构造函数》的实质衔接是：CompileInfo 只能在 BuildTilingContext 链中注入；ContextBuilder、Outputs 回退、TilingDebug 及两张空 CompileInfo 故障直接验证上下文排序约束。
- [Outputs（Utils API）](outputs.md)（`same_topic`）：CompileInfo 与《Outputs（Utils API）》的实质衔接是：CompileInfo 只能在 BuildTilingContext 链中注入；ContextBuilder、Outputs 回退、TilingDebug 及两张空 CompileInfo 故障直接验证上下文排序约束。
- [Tiling调测](../tiling_tuning.md)（`same_topic`）：CompileInfo 与《Tiling调测》的实质衔接是：CompileInfo 只能在 BuildTilingContext 链中注入；ContextBuilder、Outputs 回退、TilingDebug 及两张空 CompileInfo 故障直接验证上下文排序约束。
<!-- cannbot:related:end -->
