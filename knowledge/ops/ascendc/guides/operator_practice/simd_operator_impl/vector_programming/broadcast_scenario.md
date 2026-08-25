---
type: Guide
title: Broadcast场景
description: 在某些场景下，可能会存在两个输入shape不相同的情况。由于Add接口只支持对shape相同的输入进行计算，因此需要先对输入进行shape变换，再进行Add计算。本节将对满足Broadcast条件的输入在算子实现中的Broadcast处理进行介绍，其他场景可以参考本章节中提供的思路。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/vector_programming/broadcast_scenario.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Broadcast场景

在某些场景下，可能会存在两个输入shape不相同的情况。由于Add接口只支持对shape相同的输入进行计算，因此需要先对输入进行shape变换，再进行Add计算。本节将对满足Broadcast条件的输入在算子实现中的Broadcast处理进行介绍，其他场景可以参考本章节中提供的思路。
本节中将使用Broadcast接口，因此输入需满足该API相关约束。同时，由于硬件限制，该API的输入地址需满足32字节对齐。本节以输入维度为2、第二个轴（axis = 1）需要Broadcast为例进行说明。完整的样例代码请参见输入Broadcast的Add算子样例。
## Tiling实现
与输入shape相同的场景相比，在Tiling结构体中增加相应的成员变量，表示是否需要对输入进行Broadcast、需要对哪个维度进行Broadcast、Broadcast的轴需要扩充的倍数。因此新增四个Tiling结构体成员：
-   xLen和yLen：表示两个输入的数据长度。
-   axis：表示对输入的哪个维度进行Broadcast。
-   coef：表示Broadcast的输入需要扩维的倍数。例如，x shape为(m, 1)，y shape为(m, n)，则coef = n。如下图所示，图中相同颜色部分为单次计算的数据块。
Tiling结构体定义代码如下所示：
设需要进行Broadcast的输入长度为shorterAxisLen；不需要进行Broadcast的输入长度为totalLength。
使用shorterAxisLen进行分核计算，并使用分核后的长度与coef相乘作为totalLength的分核长度。
进行核内数据切分时，需要计算Unified Buffer数据块的数量向coef和BUFFER_NUM对齐之后的数量ubBlockAligned。
## 算子类实现
在核函数初始化阶段，根据Tiling结构体传入的参数确定对哪个输入进行Broadcast。由于针对输入的第二个轴（axis = 1）进行Broadcast，可以计算出，对于需要进行Broadcast的输入，每个核搬入数据长度为blockLength / coef。
初始化函数代码如下：
由于数据是向coef对齐的，在数据拷贝的过程中可能会出现地址不满足32字节对齐的场景，因此CopyIn函数中使用DataCopyPad（GM -> UB）、CopyOut函数中使用DataCopyPad（UB -> GM）进行数据拷贝。
CopyIn函数实现代码如下：
CopyOut函数实现代码如下：
在Compute函数中，调用Add接口前需要先对输入进行Broadcast。这里需要计算Broadcast前后的shape。基于前文提到的数据关系，可以计算得出Broadcast前后的shape分别为\{tileLength / broadcastCoef, 1\}和\{tileLength / broadcastCoef, broadcastCoef\}。在此基础上对输入进行Broadcast，并将计算结果存入临时空间中，然后进行Add计算。实现代码示例如下所示：

<!-- cannbot:related:start -->
## 相关

- [Broadcast（张量变换）](../../../../apis/simd_api/adv_api/tensor_transform/broadcast.md)（`explains`）：指南中的 Compute 阶段直接调用 Broadcast 将短 shape 扩展后再做 Add，该 API 是方案的核心执行接口。
- [GetBroadCastMaxMinTmpSize](../../../../apis/simd_api/adv_api/tensor_transform/get_broad_cast_max_min_tmp_size.md)（`explains`）：Broadcast 需要临时输出空间，Host 侧查询接口为指南中的 UB 预算和 tiling 参数提供边界。
- [303 D2 末轴分块破坏 no-Cast DAG x2 加载](../../../../runbooks/precision/broadcast_303_d2_last_axis_no_cast_dag_x2_missing.md)（`related`）：Broadcast 指南给出标量/轴广播数据组织；本卡说明 303 末轴分发后 CopyInBrc 的 x2 加载条件失配。
- [AscendC Muls cyclic-repeat 致分组 scale 错配](../../../../runbooks/precision/ascendc_muls_cyclic_repeat_scale.md)（`related`）：AscendC Muls cyclic-repeat 致分组 scale 错配 与《Broadcast场景》的实质衔接是：Muls 对短 scale 做 cyclic repeat 而分组量化需要 block repeat；Broadcast、Muls、AntiQuant、GroupedMatmul/SwiGLU 案例共同验证 scale 的连续分组映射。
- [FindSplitAxis 误传 total_slots 致 slot 翻倍](../../../../runbooks/precision/findsplitaxis_total_slots_slot.md)（`related`）：FindSplitAxis 误传 total_slots 致 slot 翻倍 与《Broadcast场景》的实质衔接是：FindSplitAxis 第四参要求 phys_nodes，传入已乘 DB 的 total_slots 会再次乘二；per-buffer UB 预算、rank/split、TilingData 和 Broadcast 卡用于核对内外切分量一致。
- [MulPreferContiguous 稀疏广播拦截失败且慢于 304](../../../../runbooks/performance/mulprefercontiguous_304.md)（`related`）：《MulPreferContiguous 稀疏广播拦截失败且慢于 304》处理“B 类稀疏广播（首轴稀疏、stride 大）触发 MulPreferContiguous 拦截转连续，baseline GetWorkspaceSize 返回 -1.0（schMode 空）或性能慢于 fixed 直接走 304 nddma_transpose_noLoop。”。《Broadcast场景》提供“在某些场景下，可能会存在两个输入shape不相同的情况。由于Add接口只支持对shape相同的输入进行计算，因此需要先对输入进行shape变换，再进行Add计算。本节将对满足Broadcast条件的输入在算子实现中的Broadcast处理进行介绍，其他场景可以参考本章节中提供的思路。”，其具体合同或探针直接接入稀疏广播输入的 contiguous 拦截、304 路由和非连续 shape/stride 合同。
- [softplus_v2_grad tiling rank 校验拒标量广播](../../../../runbooks/compilation/softplus_v2_grad_tiling_rank.md)（`related`）：指南把广播所需的轴、倍数和 tiling 数据显式下发到 kernel，补足 focal 从 host 接受异 rank 输入到 device 实施广播的后续实现链。
- [反量化 561103 实为 CheckBroadcastShape 过严](../../../../runbooks/compilation/561103_checkbroadcastshape.md)（`related`）：Broadcast 场景指南给出合法 shape 条件和索引展开，可核对 CheckBroadcastShape 的预期。
<!-- cannbot:related:end -->
