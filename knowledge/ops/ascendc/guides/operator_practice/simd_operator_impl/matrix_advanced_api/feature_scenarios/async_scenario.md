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

- [GetTensorC](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/get_tensor_c.md)（`explains`）：异步 Iterate 计算后由 GetTensorC 从 workspace/L0C 取得 C 分片，调用时点决定何时发生同步等待。
- [Iterate](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/iterate.md)（`explains`）：本指南通过 Iterate 模板参数开启异步计算，并要求结果需要时再配合 GetTensorC；Iterate 是该时序的发起接口。
- [IterateAll](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/iterate_all.md)（`explains`）：《IterateAll》说明调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。；《异步场景处理》说明Matmul的Iterate和IterateAll接口在MIX场景（包含矩阵计算和矢量计算）下提供了同步和异步两种模式，纯Cube场景（只有矩阵计算）下，只支持同步模式。。二者在IterateAll一次完成singleCoreM×singleCoreN，异步模式必须配WaitIterateAll并按GetTensorC/输出场景消费结果上存在可执行的直接衔接。
- [SetWorkspace](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/set_workspace.md)（`explains`）：Iterate 异步模式必须在调用前用 SetWorkspace 提供缓存 C 分片的临时空间；否则后续计算会覆盖尚未取出的结果。
- [WaitIterateAll](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/wait_iterate_all.md)（`explains`）：WaitIterateAll 是指南指定的 IterateAll 异步完成等待点，使后续消费者在结果真正就绪后继续。
- [AIC和AIV独立运行机制](aic_aiv_independent_execution.md)（`related`）：双主模式禁止 GetTensorC 并要求 IterateAll 输出 GM；异步场景页提供 Matmul 计算与后续矢量阶段的另一同步/输出组织方式。
- [启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖](../../../simd_operator_optimization/pipeline_scheduling/enable_iterate_avoid_sync.md)（`related`）：优化指南解释异步模式为何只在首次发送 AIV→AIC 消息并减少核间交互，还明确提醒必须设置 workspace，直接补充本卡的性能决策依据。
- [融合算子编程基础知识](../../fusion_operator_programming/cv_fusion/basics.md)（`related`）：《融合算子编程基础知识》处理“>学习融合算子编程之前，请确保已经掌握矩阵编程相关知识。”。《异步场景处理》明确“Matmul的Iterate和IterateAll接口在MIX场景（包含矩阵计算和矢量计算）下提供了同步和异步两种模式，纯Cube场景（只有矩阵计算）下，只支持同步模式。”，可直接用于核对CV 融合的数据依赖、Cube/AIV 协作、耦合模式与异步处理编程范式。
- [通用融合算子实现](../../fusion_operator_programming/general_fusion/operator_impl.md)（`related`）：通用融合算子实现 与《异步场景处理》的实质衔接是：通用融合实现依赖 AIC/AIV 分工、异步、耦合/分离、多核尾块和 double buffer 场景。
- [单次矩阵乘局部输出](single_matmul_local_output.md)（`same_topic`）：单次矩阵乘局部输出 与《异步场景处理》的实质衔接是：Partial Output 只允许 MDL 的 Iterate+GetTensorC 连续写，跳过 K 累加且禁用 Bias/IterateAll；Matmul Kernel、异步/对齐和精度材料直接约束该链。
<!-- cannbot:related:end -->
