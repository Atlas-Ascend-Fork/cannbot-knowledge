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
