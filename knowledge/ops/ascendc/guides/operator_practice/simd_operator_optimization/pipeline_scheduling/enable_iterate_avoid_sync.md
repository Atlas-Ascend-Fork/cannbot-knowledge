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

- [Iterate](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/iterate.md)（`explains`）：Iterate 与《启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖》的实质衔接是：Iterate 每次推进一块 baseM×baseN 并管理 L0C；Init/SetTensor 后需按同步模式配对 GetTensorC/Wait，IterateAll/NBatch/Batch 与异步指南给出替代执行契约。
- [IterateAll](../../../../apis/simd_api/adv_api/convolution_compute/conv3_d_kernel/iterate_all.md)（`explains`）：Conv3D IterateAll 也可按文档能力评估异步调度，不能假定与 Matmul 完全同构。
- [IterateAll](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/iterate_all.md)（`explains`）：《IterateAll》说明调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。；《启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖》说明MIX场景下推荐使用Iterate或IterateAll异步接口，减少Cube与Vector核间消息交互，降低通信开销。。二者在IterateAll一次完成singleCoreM×singleCoreN，异步模式必须配WaitIterateAll并按GetTensorC/输出场景消费结果上存在可执行的直接衔接。
- [WaitIterateAll](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/wait_iterate_all.md)（`explains`）：异步提交后必须在真正消费/释放前 WaitIterateAll。
- [Matmul高阶API开启IBShare模板共享B矩阵数据](../../best_practices/matmul_tuning_cases/matmul_ibshare_b.md)（`related`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [开启DoubleBuffer](enable_double_buffer.md)（`related`）：异步 Iterate 减少 Cube/Vector 等待，双缓冲用于覆盖搬运与计算，常组合使用。
- [异步场景处理](../../simd_operator_impl/matrix_advanced_api/feature_scenarios/async_scenario.md)（`related`）：优化指南解释异步模式为何只在首次发送 AIV→AIC 消息并减少核间交互，还明确提醒必须设置 workspace，直接补充本卡的性能决策依据。
- [算子实现](../../simd_operator_impl/matrix_advanced_api/operator_impl.md)（`related`）：算子实现 与《启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖》的实质衔接是：该指南的核心是 host tiling→kernel Matmul 对象→Set A/B→Iterate/IterateAll→End；耦合模式、异步迭代与 CUBE_ONLY 故障直接约束实现选择。
- [通过BT Buffer实现高效的bias计算](../matrix_compute/bt_buffer_bias_compute.md)（`related`）：焦点处理BT Buffer 承载 Matmul Bias 以减少搬运和等待；启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖正文说明“MIX场景下推荐使用Iterate或IterateAll异步接口，减少Cube与Vector核间消息交互，降低通信开销”。候选是 Bias 计算的可替换暂存/累加路径或减少 AIC/AIV 等待的直接优化。
- [单次矩阵乘局部输出](../../simd_operator_impl/matrix_advanced_api/feature_scenarios/single_matmul_local_output.md)（`same_topic`）：单次矩阵乘局部输出 与《启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖》的实质衔接是：Partial Output 只允许 MDL 的 Iterate+GetTensorC 连续写，跳过 K 累加且禁用 Bias/IterateAll；Matmul Kernel、异步/对齐和精度材料直接约束该链。
- [核间负载均衡](../tiling_strategy/inter_core_load_balance.md)（`same_topic`）：核间负载均衡 与《启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖》的实质衔接是：核间负载均衡通过调整拖尾核与 block 数减少尾部空闲，并与核间同步、DoubleBuffer/异步 Iterate 和具体 Matmul/Philox 分块约束共同决定并行度。
<!-- cannbot:related:end -->
