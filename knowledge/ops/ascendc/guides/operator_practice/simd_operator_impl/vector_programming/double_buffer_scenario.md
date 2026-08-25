---
type: Guide
title: DoubleBuffer场景
description: 因存在算子中多次搬入搬出数据的场景，为充分利用硬件资源，实现多流水并行，引入DoubleBuffer机制。DoubleBuffer是通过将输入数据分成大小相等的两块，充分利用AI
  Core的硬件资源，实现数据搬入、计算、数据搬出的并行执行方式。下面以“核间不均分，核内不均分”的样例为例，介绍算子中DoubleBuffer的实现。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/vector_programming/double_buffer_scenario.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# DoubleBuffer场景

因存在算子中多次搬入搬出数据的场景，为充分利用硬件资源，实现多流水并行，引入DoubleBuffer机制。DoubleBuffer是通过将输入数据分成大小相等的两块，充分利用AI Core的硬件资源，实现数据搬入、计算、数据搬出的并行执行方式。下面以“核间不均分，核内不均分”的样例为例，介绍算子中DoubleBuffer的实现。
## Tiling实现
开启DoubleBuffer后，每一个数据块会分成大小相等的两块，因此，若要开启DoubleBuffer，要求数据总量应该能够均分。为了简化处理，将可用的Unified Buffer空间以32字节为粒度，分成n块dataBlock，如果n不是偶数，则减1，这样就可以保证一套代码兼容开启或不开启DoubleBuffer功能。对应步骤如下：
1.  判断数据总长度totalLength是否满足32字节对齐，如不满足，则计算totalLength向上32字节对齐后的长度totalLengthAligned。
2.  根据totalLengthAligned，计算每个核的计算数据长度blockLength，分核策略可参照尾核切分。
3.  计算其余Tiling参数。
对当前Unified Buffer可用空间以32字节为粒度，进行切分，计算出数据块个数UB_BLOCK_NUM。根据是否开启DoubleBuffer计算出当前可用的最大数据块个数，记作MAX_AVAILABLE_UB_BLOCK_NUM。最后，以MAX_AVAILABLE_UB_BLOCK_NUM为粒度，对blockLength进行切分。为方便演示，如下代码直接给出UB_BLOCK_NUM，作为当前Unified Buffer可用空间包含的block（32字节）数。
## 算子类实现
不开启DoubleBuffer时，只需要对每个核上最后一个分块的起始地址做处理；开启DoubleBuffer后，需要处理的数据块长度变成原来的一半，所以需要对最后两个数据块的起始地址做处理。
开启DoubleBuffer，参考InitBuffer接口函数原型，将num参数配置成2，即BUFFER_NUM。
同时在计算核内每个数据块的长度时，考虑DoubleBuffer场景，需要将Buffer数量，即BUFFER_NUM=2带入计算。
由于无法保证尾块满足DoubleBuffer的条件，因此不对尾块进行切分。
Init函数实现代码如下：
由于开启DoubleBuffer后，切分后的主块数据块个数翻倍，在Process函数中，需要将BUFFER_NUM带入计算循环次数；尾块独立计算，不开启DoubleBuffer。后续主尾块在CopyIn、Compute、CopyOut阶段中的处理，与尾块均分相同。

<!-- cannbot:related:start -->
## 相关

- [InitBuffer](../../../../apis/simd_api/basic_api/resource_management/t_buf_pool/init_buffer.md)（`explains`）：DoubleBuffer场景 与《InitBuffer》的实质衔接是：DoubleBuffer 将主块拆为两份并通过 InitBuffer(...,2,...) 让搬入、计算、搬出重叠；主尾块切分材料说明尾块例外，UB 预算和 TQue/TBuf 重载故障直接约束 bufferNum 与长度配置。
- [InitBuffer](../../../../apis/simd_api/basic_api/resource_management/t_pipe/init_buffer.md)（`explains`）：DoubleBuffer场景 与《InitBuffer》的实质衔接是：DoubleBuffer 将主块拆为两份并通过 InitBuffer(...,2,...) 让搬入、计算、搬出重叠；主尾块切分材料说明尾块例外，UB 预算和 TQue/TBuf 重载故障直接约束 bufferNum 与长度配置。
- [DAV_2201 element-wise unary kernel 骨架 多核](../../../../runbooks/compilation/dav2201_elementwise_unary_kernel_skeleton_relu.md)（`related`）：DoubleBuffer场景 与《DAV_2201 element-wise unary kernel 骨架 多核》的实质衔接是：DoubleBuffer 将主块拆为两份并通过 InitBuffer(...,2,...) 让搬入、计算、搬出重叠；主尾块切分材料说明尾块例外，UB 预算和 TQue/TBuf 重载故障直接约束 bufferNum 与长度配置。
- [FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR](../../../../runbooks/compilation/fp16_double_buffer_ub_budget_queue_vs_tbuf_multiplier.md)（`related`）：FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR 与《DoubleBuffer场景》的实质衔接是：focal 的漏乘项正是 TQue/TBuf 数量×double-buffer depth×dtype字节数；DoubleBuffer文档、InitBuffer、GetCoreMemSize和按dtype分配案例共同完成预算与验证。
- [HardSwish 逐元素 kernel 的 TQue 双缓冲实现配方](../../../../runbooks/compilation/elementwise_tque_double_buffer_inplace_recipe.md)（`related`）：DoubleBuffer场景 与《HardSwish 逐元素 kernel 的 TQue 双缓冲实现配方》的实质衔接是：DoubleBuffer 将主块拆为两份并通过 InitBuffer(...,2,...) 让搬入、计算、搬出重叠；主尾块切分材料说明尾块例外，UB 预算和 TQue/TBuf 重载故障直接约束 bufferNum 与长度配置。
- [SIMD算子实现主块均分](multi_core_tiling/main_block_even_split.md)（`related`）：《SIMD算子实现主块均分》说明长度为totalLength的输入数据可以按参与计算的核数和主块长度mainTileLength均匀切分，主块均分后无剩余数据。各核处理的数据量相同，每个核处理tileNum个主块，核内只包含主块。；《DoubleBuffer场景》说明因存在算子中多次搬入搬出数据的场景，为充分利用硬件资源，实现多流水并行，引入DoubleBuffer机制。DoubleBuffer是通过将输入数据分成大小相等的两块，充分利用AI Core的硬件资源，实现数据搬入、计算、数据搬出的并行执行方式。下面以“核间不均分，核内不均分”的样例为例，介绍算子中DoubleBuffer的实现。。二者在主块均分与三种尾块策略共同覆盖多核切分分支；Kernel用GetBlockIdx定位GM段，numBlocks塌缩故障验证Host切核结果上存在可执行的直接衔接。
- [SIMD算子实现尾块均分](multi_core_tiling/tail_block_even_split.md)（`related`）：DoubleBuffer场景 与《SIMD算子实现尾块均分》的实质衔接是：DoubleBuffer 将主块拆为两份并通过 InitBuffer(...,2,...) 让搬入、计算、搬出重叠；主尾块切分材料说明尾块例外，UB 预算和 TQue/TBuf 重载故障直接约束 bufferNum 与长度配置。
- [TBuf 三参数 InitBuffer 触发 isTQue 静态断言](../../../../runbooks/compilation/tbuf_initbuffer_uses_two_arguments.md)（`related`）：DoubleBuffer场景 与《TBuf 三参数 InitBuffer 触发 isTQue 静态断言》的实质衔接是：DoubleBuffer 将主块拆为两份并通过 InitBuffer(...,2,...) 让搬入、计算、搬出重叠；主尾块切分材料说明尾块例外，UB 预算和 TQue/TBuf 重载故障直接约束 bufferNum 与长度配置。
- [TQue InitBuffer 须传深度和 uint32 长度](../../../../runbooks/compilation/tque_initbuffer_requires_depth_and_uint32_length.md)（`related`）：DoubleBuffer场景 与《TQue InitBuffer 须传深度和 uint32 长度》的实质衔接是：DoubleBuffer 将主块拆为两份并通过 InitBuffer(...,2,...) 让搬入、计算、搬出重叠；主尾块切分材料说明尾块例外，UB 预算和 TQue/TBuf 重载故障直接约束 bufferNum 与长度配置。
- [TailCoreSplit](multi_core_tiling/tail_core_split.md)（`related`）：DoubleBuffer场景 与《TailCoreSplit》的实质衔接是：DoubleBuffer 将主块拆为两份并通过 InitBuffer(...,2,...) 让搬入、计算、搬出重叠；主尾块切分材料说明尾块例外，UB 预算和 TQue/TBuf 重载故障直接约束 bufferNum 与长度配置。
- [TailCoreTailBlockSplit](multi_core_tiling/tail_core_tail_block_split.md)（`related`）：DoubleBuffer场景 与《TailCoreTailBlockSplit》的实质衔接是：DoubleBuffer 将主块拆为两份并通过 InitBuffer(...,2,...) 让搬入、计算、搬出重叠；主尾块切分材料说明尾块例外，UB 预算和 TQue/TBuf 重载故障直接约束 bufferNum 与长度配置。
- [基础矢量算子](basic_vector_operator.md)（`related`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《DoubleBuffer场景》说明因存在算子中多次搬入搬出数据的场景，为充分利用硬件资源，实现多流水并行，引入DoubleBuffer机制。DoubleBuffer是通过将输入数据分成大小相等的两块，充分利用AI Core的硬件资源，实现数据搬入、计算、数据搬出的并行执行方式。下面以“核间不均分，核内不均分”的样例为例，介绍算子中DoubleBuffer的实现。。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
- [DoubleBuffer](../../../technical_appendix/concepts_and_terms/performance_optimization/double_buffer.md)（`same_topic`）：DoubleBuffer场景 与《DoubleBuffer》的实质衔接是：DoubleBuffer 将主块拆为两份并通过 InitBuffer(...,2,...) 让搬入、计算、搬出重叠；主尾块切分材料说明尾块例外，UB 预算和 TQue/TBuf 重载故障直接约束 bufferNum 与长度配置。
- [开启DoubleBuffer](../../simd_operator_optimization/pipeline_scheduling/enable_double_buffer.md)（`same_topic`）：DoubleBuffer场景 与《开启DoubleBuffer》的实质衔接是：DoubleBuffer 将主块拆为两份并通过 InitBuffer(...,2,...) 让搬入、计算、搬出重叠；主尾块切分材料说明尾块例外，UB 预算和 TQue/TBuf 重载故障直接约束 bufferNum 与长度配置。
<!-- cannbot:related:end -->
