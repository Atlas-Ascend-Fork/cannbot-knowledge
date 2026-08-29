---
type: Guide
title: 启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖
description: MIX场景下推荐使用Iterate或IterateAll异步接口，减少Cube与Vector核间消息交互，降低通信开销。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/pipeline_scheduling/enable_iterate_avoid_sync.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖

【优先级】高
【描述】在MIX场景，即AIC（AI Cube核）和AIV（AI Vector核）混合编程中，调用Matmul Iterate或者IterateAll时，AIV发送消息到AIC启动Matmul计算。若通过Iterate同步方式，如图1同步方式消息发送示意图，每次调用都会触发一次消息发送，而通过Iterate异步方式，如异步方式消息发送示意图，仅第一次需要发送消息，后续无需发送消息，从而减少Cube与Vector核间交互，减少核间通信开销。因此，MIX场景推荐使用Iterate或者IterateAll异步接口（注意：使用异步接口时需要设置Workspace）。
【反例】
MIX场景使用Iterate接口的同步方式。
【正例】
MIX场景使用Iterate接口的异步方式。

<!-- cannbot:related:start -->
## 相关

- [Iterate](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/iterate.md)（`explains`）：【描述】在MIX场景，即AIC（AI Cube核）和AIV（AI Vector核）混合编程中，调用Matmul Iterate或者IterateAll时，AIV发送消息到AIC启动Matmul计算。若通过Iterate同步方式，如图1同步方式消息发送示意图，每次调用都会触发一次消息发送，而通过Iterate异步方式，如异步方式消息发送示意图，仅第一次需要发送消息，后续无需发送消息，从而减少Cube与Vector核间交互，减少核间通信开销。因此，MIX场景推荐使用Iterate或者IterateAll异步接口（注意：使用异步接口时需要设置Workspace）。；- sync：迭代获取C矩阵分片的过程分为同步和异步两种模式。通过该参数设置同步或者异步模式：同步模式设置为true；异步模式设置为false。默认为同步模式。具体模式的介绍和使用方法请参考GetTensorC。。Guide 给出 MIX 中选择异步 Iterate 的通信原因与 workspace 前提，API 卡给出将 sync 设为 false 的具体入口。
- [IterateAll](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/iterate_all.md)（`explains`）：【描述】在MIX场景，即AIC（AI Cube核）和AIV（AI Vector核）混合编程中，调用Matmul Iterate或者IterateAll时，AIV发送消息到AIC启动Matmul计算。若通过Iterate同步方式，如图1同步方式消息发送示意图，每次调用都会触发一次消息发送，而通过Iterate异步方式，如异步方式消息发送示意图，仅第一次需要发送消息，后续无需发送消息，从而减少Cube与Vector核间交互，减少核间通信开销。因此，MIX场景推荐使用Iterate或者IterateAll异步接口（注意：使用异步接口时需要设置Workspace）。；- sync：获取C矩阵过程分为同步和异步两种模式：同步：需要同步等待IterateAll执行结束。 异步：不需要同步等待IterateAll执行结束。 通过该参数设置同步或者异步模式：同步模式设置为true；异步模式设置为false，默认为同步模式。。Guide 给出 MIX 中选择异步 IterateAll 的通信原因与 workspace 前提，API 卡给出将 sync 设为 false 的具体入口。
- [异步场景处理](../../simd_operator_impl/matrix_advanced_api/feature_scenarios/async_scenario.md)（`related`）：异步：通过设置Iterate接口的模板参数开启异步模式。调用Iterate后，无需立即调用GetTensorC同步等待矩阵C分块搬运完成，可以先执行其它操作，待需要获取结果时再调用GetTensorC。异步模式可以减少同步等待，提高并行度，开发者对计算性能要求较高时，可以选用该方式。异步场景时，需要使用一块临时空间来缓存Iterate计算结果，否则会覆盖计算结果，调用GetTensorC时会在该临时空间中获取C的矩阵分片。临时空间通过SetWorkspace接口进行设置。SetWorkspace接口需要在Iterate接口之前调用。；MIX场景推荐使用Iterate或者IterateAll异步接口（注意：使用异步接口时需要设置Workspace）。。场景指南给出完整同步/异步调用顺序，优化指南说明选择异步能减少 AIC/AIV 消息与等待。
<!-- cannbot:related:end -->
