---
type: Guide
title: 异步场景处理
description: Matmul的Iterate和IterateAll接口在MIX场景（包含矩阵计算和矢量计算）下提供了同步和异步两种模式，纯Cube场景（只有矩阵计算）下，只支持同步模式。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/async_scenario.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 异步场景处理

## 功能介绍
Matmul的Iterate和IterateAll接口在MIX场景（包含矩阵计算和矢量计算）下提供了同步和异步两种模式，纯Cube场景（只有矩阵计算）下，只支持同步模式。
同步模式指的是程序执行时，需要等待某个操作完成后才能继续执行下一步操作。 异步模式指的是程序执行时，不需要等待某个操作完成就可以继续执行下一步操作。
-   Iterate&GetTensorC的同步和异步
-   同步：执行完一次Iterate迭代计算后，执行GetTensorC搬运矩阵C分片，搬运完成后，才能进行下一次计算。如下图所示，C矩阵中，矩阵块1搬走后，才能计算矩阵块2，矩阵块2搬运完成后，才能计算矩阵块3。
Iterate&GetTensorC同步模式的关键代码示例如下：
-   异步：通过设置Iterate接口的模板参数开启异步模式。调用Iterate后，无需立即调用GetTensorC同步等待矩阵C分块搬运完成，可以先执行其它操作，待需要获取结果时再调用GetTensorC。异步模式可以减少同步等待，提高并行度，开发者对计算性能要求较高时，可以选用该方式。异步场景时，需要使用一块临时空间来缓存Iterate计算结果，否则会覆盖计算结果，调用GetTensorC时会在该临时空间中获取C的矩阵分片。临时空间通过SetWorkspace接口进行设置。SetWorkspace接口需要在Iterate接口之前调用。
Iterate&GetTensorC异步模式的关键代码示例如下：
-   IterateAll的同步和异步
-   同步：后续操作需要同步等待IterateAll执行结束。
IterateAll同步模式的关键代码示例如下：
-   异步：后续操作不需要同步等待IterateAll执行结束，需要IterateAll的结果时，调用WaitIterateAll等待IterateAll异步接口返回。
IterateAll异步模式的关键代码示例如下：
## 使用场景
-   Iterate&GetTensorC的同步：MIX场景（包含矩阵计算和矢量计算）、纯Cube场景（只有矩阵计算）。
-   Iterate&GetTensorC的异步：仅MIX场景（包含矩阵计算和矢量计算）。
-   IterateAll的同步：MIX场景（包含矩阵计算和矢量计算）、纯Cube场景（只有矩阵计算）。
-   IterateAll的异步：仅MIX场景（包含矩阵计算和矢量计算）。
## 约束说明
-   Iterate&GetTensorC的异步场景：
-   传入的C矩阵地址空间大小需要保证不小于baseM * baseN。
-   SetWorkspace接口需要在Iterate接口之前调用。
-   支持只输出到UB（VECIN）、只输出到Global Memory，同时输出到Global Memory和UB（VECIN）三种输出方式。

<!-- cannbot:related:start -->
## 相关

- [IterateAll](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/iterate_all.md)（`explains`）：“获取C矩阵过程分为同步和异步两种模式”与“需要IterateAll的结果时，调用WaitIterateAll等待IterateAll异步接口返回”把接口参数选择落实为完整异步使用步骤。
- [启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖](../../../simd_operator_optimization/pipeline_scheduling/enable_iterate_avoid_sync.md)（`related`）：异步：通过设置Iterate接口的模板参数开启异步模式。调用Iterate后，无需立即调用GetTensorC同步等待矩阵C分块搬运完成，可以先执行其它操作，待需要获取结果时再调用GetTensorC。异步模式可以减少同步等待，提高并行度，开发者对计算性能要求较高时，可以选用该方式。异步场景时，需要使用一块临时空间来缓存Iterate计算结果，否则会覆盖计算结果，调用GetTensorC时会在该临时空间中获取C的矩阵分片。临时空间通过SetWorkspace接口进行设置。SetWorkspace接口需要在Iterate接口之前调用。；MIX场景推荐使用Iterate或者IterateAll异步接口（注意：使用异步接口时需要设置Workspace）。。场景指南给出完整同步/异步调用顺序，优化指南说明选择异步能减少 AIC/AIV 消息与等待。
<!-- cannbot:related:end -->
