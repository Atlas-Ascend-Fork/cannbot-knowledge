---
type: Guide
title: 高维切分API
description: '>- 本章节对矢量计算基础API中的tensor高维切分计算接口做解释说明。如果您不需要使用此类接口，可略过该章节。'
tags: [task.lookup, topic.implementation.api_layer]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/library_api/basic_api/interface_classification/high_dim_split_api.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 高维切分API

使用tensor高维切分计算API可充分发挥硬件优势，支持开发者控制指令的迭代执行和操作数的地址间隔，功能更加灵活。
矢量计算通过Vector计算单元完成，矢量计算的源操作数和目的操作数均通过Unified Buffer（UB）来进行存储。Vector计算单元每个迭代会从UB中取出8个datablock（每个datablock数据块内部地址连续，长度32Byte），进行计算，并写入对应的8个datablock中。下图为单次迭代内的8个datablock进行Exp计算的示意图。
-   矢量计算API支持开发者通过repeatTime来配置迭代次数，从而控制指令的多次迭代执行。假设repeatTime设置为2，矢量计算单元会进行2个迭代的计算，可计算出2 * 8（每个迭代8个datablock） * 32Byte（每个datablock32Byte） = 512Byte的结果。如果数据类型为half，则计算了256个元素。下图展示了2次迭代Exp计算的示意图。由于硬件限制，repeatTime不能超过255。
-   针对同一个迭代中的数据，可以通过mask参数进行掩码操作来控制实际参与计算的个数。下图为进行Abs计算时通过mask逐比特模式按位控制哪些元素参与计算的示意图，1表示参与计算，0表示不参与计算。
-   矢量计算单元还支持带间隔的向量计算，通过dataBlockStride（单次迭代内不同datablock间地址步长）和repeatStride（相邻迭代间相同datablock的地址步长）来进行配置。
-   dataBlockStride
如果需要控制单次迭代内，数据处理的步长，可以通过设置同一迭代内不同datablock的地址步长dataBlockStride来实现。下图给出了单次迭代内非连续场景的示意图，示例中源操作数的dataBlockStride配置为2，表示单次迭代内不同datablock间地址步长（起始地址之间的间隔）为2个datablock。
-   repeatStride
当repeatTime大于1，需要多次迭代完成矢量计算时，您可以根据不同的使用场景合理设置相邻迭代间相同datablock的地址步长repeatStride的值。
下图给出了多次迭代间非连续场景的示意图，示例中源操作数和目的操作数的repeatStride均配置为9，表示相邻迭代间相同datablock起始地址之间的间隔为9个datablock。相同datablock是指datablock在迭代内的位置相同，比如下图中的src1和src9处于相邻迭代，在迭代内都是第一个datablock的位置，其间隔即为repeatStride的数值。
下文中给出了dataBlockStride、repeatStride、mask的详细配置说明和示例。
## dataBlockStride
dataBlockStride是指同一迭代内不同datablock的地址步长。

<!-- cannbot:related:start -->
## 相关

- [Copy](../../../../../apis/simd_api/basic_api/memory_vector_compute/data_move/copy_ub_to_ub_mask_highdim_split.md)（`explains`）：Copy 与《高维切分API》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
- [DataCopy](../../../../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_gm_and_ub_highdim_split.md)（`explains`）：DataCopy 与《高维切分API》的实质衔接是：该 DataCopy 用 DataCopyParams 做 GM/UB 高维切分；slice/continuous 对照、高维 API 分类和 blockLen 窄化故障共同说明何时选用及参数类型边界。
- [高维切分（SIMD计算）](../../../../../apis/simd_api/basic_api/memory_vector_compute/simd_compute/high_dim_split.md)（`explains`）：The high-dimension split guide explains how GetDim/SetDim/GetShape/UpdateShape are composed to partition a high-dimensional tensor safely.
- [FindSplitAxis 误传 total_slots 致 slot 翻倍](../../../../../runbooks/precision/findsplitaxis_total_slots_slot.md)（`related`）：FindSplitAxis 误传 total_slots 致 slot 翻倍 与《高维切分API》的实质衔接是：FindSplitAxis 第四参要求 phys_nodes，传入已乘 DB 的 total_slots 会再次乘二；per-buffer UB 预算、rank/split、TilingData 和 Broadcast 卡用于核对内外切分量一致。
- [连续计算API](continuous_compute_api.md)（`same_topic`）：连续计算API 与《高维切分API》的实质衔接是：连续计算 API 与高维切分的选择取决于布局连续性，非对齐优化给出连续但未对齐时的可执行分支。
<!-- cannbot:related:end -->
