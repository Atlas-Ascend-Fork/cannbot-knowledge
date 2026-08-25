---
type: Guide
title: AIC和AIV独立运行机制
description: AIC和AIV独立运行机制，又称双主模式。在分离模式下，区别于MIX模式（包含矩阵计算和矢量计算）通过消息机制驱动AIC运行，双主模式为AIC和AIV独立运行代码，不依赖消息驱动，开启双主模式能够提高Matmul计算性能。默认情况下，双主模式不开启，需要通过MatmulConfig中的enableMixDualMaster参数开启。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/aic_aiv_independent_execution.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# AIC和AIV独立运行机制

## 功能介绍
AIC和AIV独立运行机制，又称双主模式。在分离模式下，区别于MIX模式（包含矩阵计算和矢量计算）通过消息机制驱动AIC运行，双主模式为AIC和AIV独立运行代码，不依赖消息驱动，开启双主模式能够提高Matmul计算性能。默认情况下，双主模式不开启，需要通过MatmulConfig中的enableMixDualMaster参数开启。
## 使用场景
算子中的矩阵计算和矢量计算相关代码独立运行，不依赖消息驱动时，可以开启双主模式，以提高Matmul计算性能。
## 约束说明
-   该功能仅支持Norm模板和MDL模板。
-   算子核函数的类型为MIX，同时AIC核数 : AIV核数为1:1。
-   算子核函数的类型为MIX，同时AIC核数 : AIV核数为1:2，且A矩阵和B矩阵同时开启IBSHARE参数。
-   同一算子中所有Matmul对象的该参数取值必须保持一致。
-   A、B、Bias矩阵只支持从Global Memory输入。
-   获取矩阵计算结果只支持调用IterateAll接口输出到GlobalTensor，即计算结果放置于Global Memory的地址，不能调用GetTensorC等接口获取结果。

<!-- cannbot:related:start -->
## 相关

- [MatmulConfig](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/matmul_config.md)（`explains`）：双主模式由 MatmulConfig::enableMixDualMaster 开启，配置必须在同一算子所有 Matmul 对象间一致。
- [中级性能优化](../../../typical_operator_cases/simd_operator_impl/matmul_leakyrelu_fusion_operator/intermediate_optimization.md)（`related`）：中级性能优化 与《AIC和AIV独立运行机制》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [单 rank mock HCCL 致 AIC+AIV SyncAll 死锁](../../../../../runbooks/compilation/rank_mock_hccl_aic_aiv_syncall.md)（`related`）：单 rank mock HCCL 致 AIC+AIV SyncAll 死锁 与《AIC和AIV独立运行机制》的实质衔接是：单 rank mock 未提供真实 HCCL 参与者，SyncAll 无法闭合；HCCL context/commit/wait 和核间同步共同支持判别。
- [异步场景处理](async_scenario.md)（`related`）：双主模式禁止 GetTensorC 并要求 IterateAll 输出 GM；异步场景页提供 Matmul 计算与后续矢量阶段的另一同步/输出组织方式。
- [融合算子编程基础知识](../../fusion_operator_programming/cv_fusion/basics.md)（`related`）：《融合算子编程基础知识》处理“>学习融合算子编程之前，请确保已经掌握矩阵编程相关知识。”。《AIC和AIV独立运行机制》明确“AIC和AIV独立运行机制，又称双主模式。在分离模式下，区别于MIX模式（包含矩阵计算和矢量计算）通过消息机制驱动AIC运行，双主模式为AIC和AIV独立运行代码，不依赖消息驱动，开启双主模式能够提高Matmul计算性能。默认情况下，双主模式不开启，需要通过MatmulConfig中的enableMixDualMaster参数开启。”，可直接用于核对CV 融合的数据依赖、Cube/AIV 协作、耦合模式与异步处理编程范式。
- [通用融合算子实现](../../fusion_operator_programming/general_fusion/operator_impl.md)（`related`）：通用融合算子实现 与《AIC和AIV独立运行机制》的实质衔接是：通用融合实现依赖 AIC/AIV 分工、异步、耦合/分离、多核尾块和 double buffer 场景。
<!-- cannbot:related:end -->
