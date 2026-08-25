---
type: API
title: IterateAll
description: 通过设置Output在GM上的首地址，一次性计算单核卷积输出数据块并写入结果矩阵。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Kernel/IterateAll.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# IterateAll

通过设置结果矩阵Output在GM上的首地址，本接口一次性计算singleCo * singleDo * singleM大小的数据块，并写到结果矩阵Output中。 本接口提供单核内卷积计算能力，singleCo为多核切分后单个核内的输出通道大小；singleDo为多核切分后单个核内的Dout大小；singleM为多核切分后单个核内的M大小。singleCo、singleDo和singleM的大小通过SetSingleOutputShape接口设置。

函数原型：__aicore__ inline void IterateAll(const AscendC::GlobalTensor<OutputT>& output, bool enPartialSum = false)

参数：
- output（输入）：Output在GM上的地址。类型为GlobalTensor。结果矩阵Output支持的数据类型为：half、bfloat16_t。
- enPartialSum（输入）：预留参数。

约束：
- IterateAll 仅支持单 batch；多 batch 场景需逐 batch 调用 SetInput、IterateAll 和 End。
- IterateAll接口必须在初始化接口及输入输出配置接口之后进行调用，完成Conv3D计算，调用顺序如下。 ... 输入输出配置 IterateAll(...);

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Matmul高阶API开启IBShare模板共享B矩阵数据](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_ibshare_b.md)（`explains`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《IterateAll》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖](../../../../../guides/operator_practice/simd_operator_optimization/pipeline_scheduling/enable_iterate_avoid_sync.md)（`explains`）：Conv3D IterateAll 也可按文档能力评估异步调度，不能假定与 Matmul 完全同构。
- [算子实现](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/operator_impl.md)（`explains`）：算子实现 与《IterateAll》的实质衔接是：该指南的核心是 host tiling→kernel Matmul 对象→Set A/B→Iterate/IterateAll→End；耦合模式、异步迭代与 CUBE_ONLY 故障直接约束实现选择。
- [IterateAll](../../cube_compute/matmul_kernel/iterate_all.md)（`related`）：Matmul 同名接口异步/输出契约不同，不能直接套用。
- [SetInput](set_input.md)（`related`）：SetInput 完成每批输入绑定后，IterateAll 才执行该批完整 Conv3D 计算；多 batch 时明确需要重复 SetInput—IterateAll—End。
- [SetSingleOutputShape](set_single_output_shape.md)（`related`）：SetSingleOutputShape 与《IterateAll》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [SetWeight](set_weight.md)（`related`）：SetWeight 与其他输入输出配置完成后才能调用 IterateAll；后者消费已绑定权重完成单核 singleCo×singleDo×singleM 计算。
- [卷积计算Init](init.md)（`related`）：Init 建立 Conv3D Kernel 对象状态后，IterateAll 才执行完整卷积计算，二者构成明确的初始化—执行顺序。
- [Conv3D Kernel侧接口](conv3d_kernel.md)（`same_topic`）：Kernel 对象页定义 IterateAll 所属生命周期。
- [卷积计算End](end.md)（`same_topic`）：卷积计算End 与《IterateAll》的实质衔接是：Conv3D 完成 Iterate/GetTensorC 后必须调用 End 清理 EventID 和内部临时内存；Init、模板、usage 及其他卷积 End 入口共享这一成对生命周期。
<!-- cannbot:related:end -->
