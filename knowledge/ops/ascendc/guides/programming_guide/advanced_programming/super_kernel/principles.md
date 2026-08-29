---
type: Guide
title: SuperKernel原理介绍
description: SuperKernel是一种算子的二进制融合技术。与源码融合不同，它聚焦于内核函数（Kernel）的二进制调度方案优化，在已编译的二进制代码基础上，将多个子Kernel融合创建出一个超级Kernel函数（简称SuperKernel），由该SuperKernel以子函数调用的方式整合多个内核函数，从而优化计算任务、提升性能和资源利用率。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/super_kernel/principles.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# 原理介绍

## 概述
SuperKernel是一种算子的二进制融合技术。与源码融合不同，它聚焦于内核函数（Kernel）的二进制调度方案优化，在已编译的二进制代码基础上，将多个子Kernel融合创建出一个超级Kernel函数（简称SuperKernel），由该SuperKernel以子函数调用的方式整合多个内核函数，从而优化计算任务、提升性能和资源利用率。
与单算子下发相比，SuperKernel技术能够减少Task调度的等待时间和调度开销，同时利用Task间隙资源进一步优化算子头开销，提升推理性能。
开启SuperKernel融合优化后，系统会自动识别图内可被融合的算子，并生成SuperKernel进行计算。同时框架提供标定SuperKernel范围的能力，支持用户根据实际业务需求对融合范围内的算子进行标记和优化配置。
## 性能收益来源
相对于单算子下发，SuperKernel主要通过以下方式带来性能收益：
- 减少Kernel启动开销：原本需要多次启动的子Kernel，被统一通过一次SuperKernel启动完成，减少了任务调度开销。
- 减少Task调度等待时间：避免了多个独立Task之间的调度间隙。
- 算子间流水并行：通过SuperKernel内提供的任务间同步接口（SetNextTaskStart、WaitPreTaskEnd），可以让子Kernel之间的部分指令实现并行执行，进一步压缩端到端耗时。
## 支持的开启方式
当前SuperKernel特性通过PyTorch图模式开启，主要有如下两种方式：
开启方式：说明
npugraph_ex后端：在torch.compile的options中传入super_kernel_optimize=True开启SuperKernel融合；如需控制融合范围，可通过torch.npu.super_kernel_scope_begin/end进行标定。具体请参考SuperKernel功能。
GE图模式：通过torchair.scope.super_kernel作用域标定融合范围，配合TorchAir的CompilerConfig开启。具体请参考图内标定SuperKernel范围。
## 算子适配说明
CANN包发布的主流模型常用算子已支持SuperKernel融合。用户自定义的Ascend C算子如需支持SuperKernel，需要满足一定适配条件，参考如下算子适配和自验证说明：
- 算子适配说明：算子要融合进SuperKernel需要满足的通用约束（与具体的开启方式无关）。
- 算子自验证说明：在两种PyTorch图模式下分别对单个算子进行SuperKernel融合验证的样例。
- 核函数直调算子额外适配说明：对于使用>>方式开发的Ascend C算子，进入SuperKernel前需要进行的额外适配工作。

<!-- cannbot:related:start -->
## 相关

- [SK_BIND（SuperKernel）](../../../../apis/utils_api/super_kernel/sk_bind.md)（`explains`）：核函数直调算子额外适配说明：对于使用>>方式开发的Ascend C算子，进入SuperKernel前需要进行的额外适配工作。；本接口为算子SuperKernel场景提供绑定原核函数和SK子函数的能力。核函数直调算子的完整适配方法请参见核函数直调算子额外适配说明。；焦点指向的直调适配由 SK_BIND 提供原 Kernel 与 SK 子函数绑定合同。
- [SetNextTaskStart](../../../../apis/simd_api/basic_api/sync_control/inter_task_sync/set_next_task_start.md)（`explains`）：算子间流水并行：通过SuperKernel内提供的任务间同步接口（SetNextTaskStart、WaitPreTaskEnd），可以让子Kernel之间的部分指令实现并行执行，进一步压缩端到端耗时。；在SuperKernel的子Kernel中调用，调用后的指令可以和后续其他的子Kernel实现并行，提升整体性能。；目标接口实现焦点所述的后向子 Kernel 并行起点。
- [WaitPreTaskEnd](../../../../apis/simd_api/basic_api/sync_control/inter_task_sync/wait_pre_task_end.md)（`explains`）：算子间流水并行：通过SuperKernel内提供的任务间同步接口（SetNextTaskStart、WaitPreTaskEnd），可以让子Kernel之间的部分指令实现并行执行，进一步压缩端到端耗时。；在SuperKernel的子Kernel中调用，调用前的指令可以和前序其他的子Kernel实现并行，提升整体性能。；目标接口实现焦点所述的前序子 Kernel 重叠边界。
- [SuperKernel](../../../../../../model/inference/concepts/techniques/superkernel.md)（`related`）：TorchAir `ge_graph`（max-autotune）图模式下，**按用户声明的 scope 将计算子图整体融合为单个大 kernel** 的优化能力。；减少Kernel启动开销：原本需要多次启动的子Kernel，被统一通过一次SuperKernel启动完成，减少了任务调度开销。概念卡定义框架侧能力，指南解释二进制融合的启动与调度收益来源。
- [核函数直调算子额外适配说明](kernel_direct_call_adaptation.md)（`related`）：核函数直调算子额外适配说明：对于使用>>方式开发的Ascend C算子，进入SuperKernel前需要进行的额外适配工作。；对于使用>>方式开发的Ascend C算子，除了遵循算子适配说明中的通用约束外，还需要在算子Kernel入口侧增加SuperKernel入口函数。本文档介绍具体的适配方法。；目标指南展开焦点明确列出的直调算子额外适配路径。
- [算子适配说明](operator_adaptation.md)（`related`）：算子适配说明：算子要融合进SuperKernel需要满足的通用约束（与具体的开启方式无关）。；自定义算子要支持融合进SuperKernel，开发流程上与普通算子并无显著差异，但需要遵循以下一系列特定约束。；目标指南展开焦点概述的自定义算子通用适配约束。
<!-- cannbot:related:end -->
