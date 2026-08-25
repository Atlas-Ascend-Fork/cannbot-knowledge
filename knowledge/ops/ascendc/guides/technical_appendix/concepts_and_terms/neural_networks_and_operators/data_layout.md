---
type: Guide
title: 数据排布格式
description: 数据排布格式（Data Layout Format）是深度学习中对多维Tensor在内存中存储方式的描述。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/technical_appendix/concepts_and_terms/neural_networks_and_operators/data_layout.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 数据排布格式

数据排布格式（Data Layout Format）是深度学习中对多维Tensor在内存中存储方式的描述。
常见的数据格式包括ND、NHWC和NCHW等，为Tensor的每个轴赋予了特定的业务语义。
除了上述NHWC和NCHW格式外，还存在一些特殊的私有数据格式，如FRACTAL_NZ（也简称NZ）、NC1HWC0、FRACTAL_Z、NDC1HWC0、FRACTAL_Z_3D等。这些格式的引入是为了满足AI Core中Cube计算单元的高性能计算需求，通过优化内存布局，这些格式能够提升计算效率。在使用矩阵乘、卷积API开发相关算子的过程中，您可以看到这些格式的具体应用。
## 普通格式
-   ND、NHWC和NCHW
数据排布格式最初用于表示图像在内存中的存储方式，其中常见的包括ND、NHWC和NCHW。在一般情况下，所有的Tensor都是N维的（ND），而NHWC和NCHW则是为四维Tensor中的每个轴赋予了特定的业务语义，例如高度（Height）、宽度（Width）和通道数（Channels）。
NHWC和NCHW的主要区别在于通道（Channel）维度的位置：
-   NHWC格式中，通道维度位于最后一个位置。
-   NCHW格式中，通道维度位于高度和宽度之前。
具体解释每个轴的含义：
-   N：Batch数量，表示图像的数目。
-   H：Height，图像的高度，即垂直方向的像素个数。
-   W：Width，图像的宽度，即水平方向的像素个数。
-   C：Channels，图像的通道数，例如彩色RGB图像的Channels为3。
如图1所示，以一张格式为RGB的图片为例，NCHW中，C排列在外层，实际存储的是“RRRRRRGGGGGGBBBBBB”，即同一通道的所有像素值顺序存储在一起；而NHWC中C排列在最内层，实际存储的则是“RGBRGBRGBRGBRGBRGB”，即多个通道的同一位置的像素值顺序存储在一起。
尽管存储的数据相同，但不同的存储顺序会导致数据的访问特性不一致，因此即便进行同样的运算，相应的计算性能也会不同。
-   NDHWC和NCDHW
NDHWC和NCDHW是五维Tensor，较NHWC和NCHW多了一个D的维度，D代表特征深度（Depth），表示数据在深度方向上的扩展，如视频的时间步或医学图像的深度层，因此该类格式便于在时间维度上进行卷积操作。以NDHWC为例，其数据格式如下图所示：
## 矩阵乘相关特殊格式
使用Mmad基础API进行矩阵乘计算时，对矩阵输入输出的数据排布格式有一定的要求，如下图所示，要求A矩阵（位于L0A Buffer）为FRACTAL_ZZ，B矩阵（位于L0B Buffer）为FRACTAL_ZN，C矩阵（位于L0C Buffer）为FRACTAL_NZ。这些格式将矩阵划分成了一些分形（Fractal Matrix），适配Cube计算单元每次读取(16, 16)× (16, 16)的数据进行计算的硬件特点（以half数据类型为例），从而提高矩阵计算的效率。

<!-- cannbot:related:start -->
## 相关

- [Layout数据结构](../../../../apis/simd_api/basic_api/data_structure_tensor_api/layout_structure/layout_structure.md)（`explains`）：数据排布格式说明数据排布格式（Data Layout Format）是深度学习中对多维Tensor在内存中存储方式的描述。
- [TransDataTo5HD](../../../../apis/simd_api/basic_api/memory_vector_compute/data_layout_conversion/trans_data_to5_hd.md)（`explains`）：TransDataTo5HD 与《数据排布格式》的实质衔接是：TransDataTo5HD 将张量转为 NC1HWC0；布局转换/格式说明、TransData 与 C API AscTransto5hd共同确定源目格式和对应入口。
- [layout](../../../../apis/simd_api/basic_api/aux_data_structures/layout/layout1.md)（`explains`）：layout 与《数据排布格式》的实质衔接是：Layout 同时承载 shape、stride 与 format，由 MakeLayout 构造并通过 Get/Set 访问；Crd2Idx、排布格式与 NDExtLayout 方向故障验证其寻址语义。
- [数据排布转换](../../../../apis/simd_api/basic_api/memory_vector_compute/data_layout_conversion/data_layout_conversion.md)（`explains`）：数据排布转换 与《数据排布格式》的实质衔接是：数据布局转换需在 TransData/Transpose 等入口之间按源目格式选择；所选精度卡直接揭示 stride、NZ 物理布局与转换边界错误。
- [B16 交错 DINTLV 成对归零 — 转 fp32 后重排](../../../../runbooks/precision/b16_interleave_compute_should_promote_to_b32_layout.md)（`related`）：B16 交错 DINTLV 成对归零 — 转 fp32 后重排说明B16 直接解交错经 Cast 后 lane 对不齐；先转连续 fp32 UB 再走 DINTLV_B32。
- [noTrans extract 与 NDExtLayoutPtn 方向不匹配](../../../../runbooks/precision/notrans_extract_ndextlayoutptn.md)（`related`）：noTrans extract 与 NDExtLayoutPtn 方向不匹配说明aclblasStrsm blocked 路径 noTrans misaligned 尝试 extract A/B 到对齐 workspace 再走 GEMM(transA=0)，extract 行主序存储与 blocked GEMM 的 NDExtLayoutPtn 读取方向不一致致精度大错（outliers 占比 48%~69%）；trans path 靠 transA=1 转置存储恰好匹配而工作；noTrans misaligned 一律回退 SIMT，extract+GEMM 路线 banned。
- [算子基本概念](operator_basics.md)（`related`）：算子基本概念：算子名称/类型/Tensor/Shape/Layout概念是原型定义和功能设计的输入语言；数据排布卡进一步解释Tensor layout，帮助把概念落到注册与实现。 目标卡《数据排布格式》补充：数据排布格式（Data Layout Format）是深度学习中对多维Tensor在内存中存储方式的描述。
<!-- cannbot:related:end -->
