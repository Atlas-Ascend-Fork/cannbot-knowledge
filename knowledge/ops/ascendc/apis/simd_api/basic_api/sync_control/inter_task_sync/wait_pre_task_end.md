---
type: API
title: WaitPreTaskEnd
description: 算子层面支持SuperKernel特性Early-Start能力的接口，在子Kernel中调用后，调用前的指令可与前序子Kernel并行执行，提升整体性能。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.synchronization
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/inter_task_sync/WaitPreTaskEnd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a3
source_headers:
- include/basic_api/kernel_operator_common_intf.h
---

# WaitPreTaskEnd<a name="ZH-CN_TOPIC_0000002337883177"></a>

> [!NOTE]说明 
>本接口为试验接口，在后续版本中可能会调整或改进，不保证后续兼容性。请开发者在使用过程中关注后续版本更新。

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_operator_common_intf.h"`。

算子层面支持SuperKernel特性Early-Start能力的接口，调用后在TorchAir层面：1.GE图模式下进行默认启用; 2.npugraph_ex后端通过early_start选项进行控制启用。

在[SuperKernel](../../../../../guides/programming_guide/advanced_programming/super_kernel/principles.md)的子核函数（Kernel）中调用，调用前的指令可以和前序其他的子核函数（Kernel）实现并行，提升整体性能。如[图1](#fig99271836191110)所示，SuperKernel按序调用子核函数（Kernel），为保证子核函数（Kernel）之间数据互不干扰，会在子核函数（Kernel）间插入算子间同步进行保序，子核函数（Kernel）<sub>N+1</sub>调用该接口之前的指令会和前序子核函数（Kernel）<sub>N</sub>实现并行。

SuperKernel是一种算子的二进制融合技术，与源码融合不同，它聚焦于核函数（Kernel） \(核函数（Kernel）\)的二进制的调度方案，展开深度优化，于已编译的二进制代码基础上融合创建一个超级核函数（Kernel）（SuperKernel），以调用子函数的方式调用多个其他核函数（Kernel），也就是子核函数（Kernel）。相对于单算子下发，SuperKernel技术可以减少任务调度等待时间和调度开销，同时利用Task间隙资源进一步优化算子头开销。

**开发者需要自行保证调用此接口前的指令不会与前序算子互相干扰而导致精度问题，推荐在整个算子第一条搬运指令前调用此接口。**

**图1**  通过WaitPreTaskEnd实现并行示意图<a name="fig99271836191110"></a>  
![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/wait_pre_task_end_parallel_diagram.png "通过WaitPreTaskEnd实现并行示意图")

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template<bool FORCE = false>
__aicore__ inline void WaitPreTaskEnd()
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| FORCE | 离线编译时是否强制启用Early-Start能力，不影响在线编译。<br>false：离线编译时不强制启用Early-Start能力；<br>true：离线编译时启用Early-Start能力，适用于无在线编译流程的算子（如<<<>>>开发的算子）。 |

## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

- 该接口适用于TorchAir图模式开发场景，且需在启用SuperKernel特性后方可生效。具体内容请参考[图内标定SuperKernel范围](https://www.hiascend.com/document/detail/zh/Pytorch/latest/devguide/TorchAir/docs/zh/ascend_ir/features/advanced/super_kernel_scope.md)。
- 在算子运行过程中，需要保证此接口在每个核上都被调用，且每个核上仅被调用一次。
- 若子核函数（Kernel）某个TilingKey分支调用了此接口，则开发者需要保证当前算子可能会运行的所有TilingKey均调用了此接口，否则会出现因同步指令数量不匹配而卡住的现象。

## 调用示例<a name="section837496171220"></a>

```cpp
AscendC::LocalMemAllocator<AscendC::Hardware::UB> ubAllocator;
AscendC::LocalTensor<T> src0Local = ubAllocator.Alloc<T, TOTAL_LENGTH>();
AscendC::LocalTensor<T> src1Local = ubAllocator.Alloc<T, TOTAL_LENGTH>();
AscendC::LocalTensor<T> dstLocal = ubAllocator.Alloc<T, TOTAL_LENGTH>();

// 在第一条搬运指令前调用，使之前的指令可与前序子kernel并行执行。
AscendC::WaitPreTaskEnd();

AscendC::DataCopy(src0Local, src0Global, TOTAL_LENGTH);
AscendC::DataCopy(src1Local, src1Global, TOTAL_LENGTH);
AscendC::SetFlag<AscendC::HardEvent::MTE2_V>(EVENT_ID0);
AscendC::WaitFlag<AscendC::HardEvent::MTE2_V>(EVENT_ID0);

AscendC::Add(dstLocal, src0Local, src1Local, TOTAL_LENGTH);
```

完整样例请参考[TaskSync样例](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/03_basic_api/05_sync_control/task_sync)。


<!-- cannbot:related:start -->
## 相关

- [SuperKernel原理介绍](../../../../../guides/programming_guide/advanced_programming/super_kernel/principles.md)（`explains`）：算子间流水并行：通过SuperKernel内提供的任务间同步接口（SetNextTaskStart、WaitPreTaskEnd），可以让子Kernel之间的部分指令实现并行执行，进一步压缩端到端耗时。；在SuperKernel的子Kernel中调用，调用前的指令可以和前序其他的子Kernel实现并行，提升整体性能。；目标接口实现焦点所述的前序子 Kernel 重叠边界。
- [SetNextTaskStart](set_next_task_start.md)（`related`）：在SuperKernel的子Kernel中调用，调用后的指令可以和后续其他的子Kernel实现并行，提升整体性能。；在SuperKernel的子Kernel中调用，调用前的指令可以和前序其他的子Kernel实现并行，提升整体性能。。SetNextTaskStart 放开当前子 Kernel 尾部与后继并行，WaitPreTaskEnd 放开当前子 Kernel 头部与前序并行；二者从相邻两侧共同定义 SuperKernel Early-Start 重叠区间。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 2 / 2 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [QuantMatmulReduceSumWeightNz A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/quant_matmul_reduce_sum_weight_nz.md)（`related`）：算子声明的固定版本源码包含对 `WaitPreTaskEnd(...)` 的直接调用（第 195 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/quant_matmul_reduce_sum/op_kernel/quant_matmul_reduce_sum.h#L195)
- [GroupedMatmul A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul.md)（`related`）：算子声明的固定版本源码包含对 `WaitPreTaskEnd(...)` 的直接调用（第 286 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul/op_kernel/grouped_matmul.h#L286)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
