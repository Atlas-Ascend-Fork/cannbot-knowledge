---
type: Guide
title: 算子实现
description: 介绍使用Matmul高阶API实现矩阵乘算子的流程，包括Host侧Tiling参数获取与Kernel侧矩阵乘操作。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_advanced_api/operator_impl.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 算子实现

## 实现流程
上文介绍了Matmul矩阵乘的数据切分方案和数据流。Ascend C提供一组Matmul高阶API，封装了这些常用的切分和数据搬运、计算的算法逻辑，方便用户快速实现Matmul矩阵乘法的运算操作。开发者在host侧通过调用API自动获取Tiling参数，该参数传递到kernel侧后，在初始化操作时传入，通过几个简单的API即可完成矩阵乘操作。完整样例请参考LINK。
host侧自动获取Tiling参数的关键步骤介绍如下：
1.  创建Tiling对象。
传入硬件平台信息创建PlatformAscendC对象，然后创建Tiling对象，硬件平台信息可以通过GetPlatformInfo获取。
2.  设置参与Matmul运算的核数，A、B的内存逻辑位置、格式和数据类型。
3.  设置矩阵shape信息。
4.  设置可用空间大小信息。
设置Matmul计算时可用的L1 Buffer/L0C Buffer/Unified Buffer空间大小，-1表示AI处理器对应Buffer的大小。
5.  获取Tiling参数。
6.  Tiling参数的序列化保存等其他操作。
kernel侧使用Matmul API矩阵乘运算的具体步骤如下：
1.  创建Matmul对象
创建Matmul对象的示例如下：
-   纯Cube模式（只有矩阵计算）场景下，建议在代码中定义ASCENDC_CUBE_ONLY宏，避免额外的性能开销。本节内容以纯Cube模式举例。
-   默认为MIX模式（包含矩阵计算和矢量计算），该场景下通常不定义ASCENDC_CUBE_ONLY宏，如果在程序中使用了ASCENDC_CUBE_ONLY宏，则必须使用ASCEND_IS_AIC宏和ASCEND_IS_AIV宏将Cube计算和Vector计算隔离开，更多内容请参考融合算子编程。
创建对象时需要传入A、B、C的参数类型信息，类型信息通过MatmulType来定义，包括：内存逻辑位置、数据格式、数据类型。
2.  初始化操作。
3.  设置左矩阵A、右矩阵B。
4.  完成矩阵乘操作。
-   调用Iterate完成单次迭代计算，叠加while循环完成单核全量数据的计算。Iterate方式，可以自行控制迭代次数，完成所需数据量的计算，方式比较灵活。
-   调用IterateAll完成单核上所有数据的计算。IterateAll方式，无需循环迭代，使用比较简单。
5.  结束矩阵乘操作。
## 设置Shape信息
在实现Host Tiling时可以设置Shape信息，用于Tiling计算；kernel侧运行时也可以修改部分Shape信息，用于尾块设置、Matmul复用（多个Matmul计算复用一个Matmul对象）等场景。本节对涉及到的Shape概念进行介绍，并给出host侧和kernel侧设置Tiling信息的指导。

<!-- cannbot:related:start -->
## 相关

- [Iterate](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/iterate.md)（`explains`）：Iterate 与《算子实现》的实质衔接是：Iterate 每次推进一块 baseM×baseN 并管理 L0C；Init/SetTensor 后需按同步模式配对 GetTensorC/Wait，IterateAll/NBatch/Batch 与异步指南给出替代执行契约。
- [Iterate](../../../../apis/simd_api/adv_api/hccl_communication/hccl_kernel/iterate.md)（`explains`）：算子实现 与《Iterate》的实质衔接是：该指南的核心是 host tiling→kernel Matmul 对象→Set A/B→Iterate/IterateAll→End；耦合模式、异步迭代与 CUBE_ONLY 故障直接约束实现选择。
- [IterateAll](../../../../apis/simd_api/adv_api/convolution_compute/conv3_d_kernel/iterate_all.md)（`explains`）：算子实现 与《IterateAll》的实质衔接是：该指南的核心是 host tiling→kernel Matmul 对象→Set A/B→Iterate/IterateAll→End；耦合模式、异步迭代与 CUBE_ONLY 故障直接约束实现选择。
- [IterateAll](../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/iterate_all.md)（`explains`）：《IterateAll》说明调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。；《算子实现》说明介绍使用Matmul高阶API实现矩阵乘算子的流程，包括Host侧Tiling参数获取与Kernel侧矩阵乘操作。。二者在IterateAll一次完成singleCoreM×singleCoreN，异步模式必须配WaitIterateAll并按GetTensorC/输出场景消费结果上存在可执行的直接衔接。
- [Iterate（卷积计算）](../../../../apis/simd_api/adv_api/convolution_compute/conv3_d_backprop_filter_kernel/iterate.md)（`explains`）：算子实现 与《Iterate（卷积计算）》的实质衔接是：该指南的核心是 host tiling→kernel Matmul 对象→Set A/B→Iterate/IterateAll→End；耦合模式、异步迭代与 CUBE_ONLY 故障直接约束实现选择。
- [ASCENDC_CUBE_ONLY 入口须 __aicore__](../../../../runbooks/compilation/ascendc_cube_only_aicore.md)（`related`）：算子实现 与《ASCENDC_CUBE_ONLY 入口须 __aicore__》的实质衔接是：该指南的核心是 host tiling→kernel Matmul 对象→Set A/B→Iterate/IterateAll→End；耦合模式、异步迭代与 CUBE_ONLY 故障直接约束实现选择。
- [Matmul特性介绍](feature_scenarios/matmul_features.md)（`related`）：算子实现 与《Matmul特性介绍》的实质衔接是：该指南的核心是 host tiling→kernel Matmul 对象→Set A/B→Iterate/IterateAll→End；耦合模式、异步迭代与 CUBE_ONLY 故障直接约束实现选择。
- [SIMD算子实现概述](../overview.md)（`related`）：算子实现 与《SIMD算子实现概述》的实质衔接是：该指南的核心是 host tiling→kernel Matmul 对象→Set A/B→Iterate/IterateAll→End；耦合模式、异步迭代与 CUBE_ONLY 故障直接约束实现选择。
- [SIMD算子实现耦合模式](../matrix_basic_api/coupled_mode.md)（`related`）：《SIMD算子实现耦合模式》说明>本节内容为针对耦合模式，使用基础API进行矩阵乘法的编程指导。；《算子实现》说明介绍使用Matmul高阶API实现矩阵乘算子的流程，包括Host侧Tiling参数获取与Kernel侧矩阵乘操作。。二者在耦合Cube范式的CopyIn/Split/Compute/CopyOut直接由DataCopy、LoadData、Mmad和TQue交接实现上存在可执行的直接衔接。
- [启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖](../../simd_operator_optimization/pipeline_scheduling/enable_iterate_avoid_sync.md)（`related`）：算子实现 与《启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖》的实质衔接是：该指南的核心是 host tiling→kernel Matmul 对象→Set A/B→Iterate/IterateAll→End；耦合模式、异步迭代与 CUBE_ONLY 故障直接约束实现选择。
- [融合算子编程基础知识](../fusion_operator_programming/cv_fusion/basics.md)（`related`）：《融合算子编程基础知识》处理“>学习融合算子编程之前，请确保已经掌握矩阵编程相关知识。”。《算子实现》明确“介绍使用Matmul高阶API实现矩阵乘算子的流程，包括Host侧Tiling参数获取与Kernel侧矩阵乘操作。”，可直接用于核对CV 融合的数据依赖、Cube/AIV 协作、耦合模式与异步处理编程范式。
- [高级编程基本流程](../../../programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/kernel_operator_implementation.md)（`related`）：算子实现 与《高级编程基本流程》的实质衔接是：该指南的核心是 host tiling→kernel Matmul 对象→Set A/B→Iterate/IterateAll→End；耦合模式、异步迭代与 CUBE_ONLY 故障直接约束实现选择。
- [SIMD算子实现分离模式](../matrix_basic_api/decoupled_mode.md)（`same_topic`）：算子实现 与《SIMD算子实现分离模式》的实质衔接是：该指南的核心是 host tiling→kernel Matmul 对象→Set A/B→Iterate/IterateAll→End；耦合模式、异步迭代与 CUBE_ONLY 故障直接约束实现选择。
- [SIMD算子实现基础知识](basics.md)（`same_topic`）：算子实现 与《SIMD算子实现基础知识》的实质衔接是：该指南的核心是 host tiling→kernel Matmul 对象→Set A/B→Iterate/IterateAll→End；耦合模式、异步迭代与 CUBE_ONLY 故障直接约束实现选择。
<!-- cannbot:related:end -->
