---
type: Guide
title: 拼接与拆分复制：空输入、布局和融合门控
description: 对照Cat的空张量过滤与主线Dimname守卫、ChunkCat的SoC与dtype快路，以及SplitWithSizesCopy两代融合门和主线新增本地检查。
tags:
- task.implementation
- topic.compute.composite
- topic.data_movement.data_copy
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/CatKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ChunkCatKernelOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SplitWithSizesCopyNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/CatKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ChunkCatKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SplitWithSizesCopyNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp
  role: implementation
created_at: '2026-11-12T02:58:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 拼接与拆分复制：空输入、布局和融合门控

Cat、ChunkCat和SplitWithSizesCopy的SDK路径有不同选择条件。命名中的“copy”或“cat”不能说明一定走融合内核；原生ATen委托也不能直接写成CPU回退。

## Cat的空张量过滤与输出准备

两版Cat先经过普通兼容宏，再materialize输入列表、拒绝0维Tensor，并过滤**一维且长度0**的输入；其他空shape不会被这个过滤器一概删掉。functional的result_type却根据完整materialized列表计算，正常路径按首个未过滤输入的options加该dtype申请输出；out使用第一个原输入及计算shape检查，没有同样的显式result_type参数。

全部被过滤时，functional直接按首个原输入申请结果，已计算的high_type没有用于这次申请；out只按{0}检查后返回。该早退在轴包装、names推导和SDK调用之前，不等于空列表也安全：本地仍访问materialized[0]。非空路线的尺寸helper沿拼接轴求和，其他轴取首个未跳过Tensor；它自己没有逐项验证其余轴一致性。

make_warp_dim只在rank≤0时把基数设1，负dim加一次基数后返回，不检查最终上下界。正常Cat在形状helper前推导输出names、SDK后传播names；不能把这层局部维度处理写成完整合法性认证。主线Dimname重载及Schema只保留V2R1..V2R12，发布无该本地守卫并列all_version。

## ChunkCat：先检查符号，再看布局与dtype

| 条件 | 本地选择与可见准备 |
| --- | --- |
| 静态双符号探测失败 | 直接委托at::native::_chunk_cat或其out；发布探测条件还要求SoC枚举<Ascend950，主线移除此额外条件 |
| 主线探测成功 | 先调用上游preprocess_chunk_cat_inputs得到wrapped_dim；发布直接使用原dim，没有这次本地预处理调用 |
| functional快路 | 所有输入contiguous、**首个**输入dtype为Float/Half/BFloat16、处理后的dim==0，调用aclnnChunkCat；否则已申请结果后委托native out |
| out快路 | 额外要求记录下来的输入及out连续性、首输入与out同device、允许的dtype组合；Float输入只配Float输出，Half/BFloat16输入可配这三种输出。先记录连续性再check_tensor |

输出shape保留首输入dim之前的前缀，在dim放num_chunks，末维将每个输入`ceil(size(dim)/num_chunks)`乘后续轴长度后相加。helper仅在num_chunks>0时累计列数，且直接访问tensors[0]/size(dim)，不能用它替代完整参数检查；主线预处理函数的内部实现不在此扩展。

functional按推导shape与首输入dtype申请结果，代码没有显式把所有输入转成out dtype；out的类型组合检查也不是已经完成cast的证据。进入native out的慢路前可能已有输出申请/检查，不能仅把SDK执行时间视为整次调用耗时。

## SplitWithSizesCopy的两个SDK门

两版旧fused gate要求调用`is_gte_cann_version_830rc1()`为真、self二维、分段数**33..64**、物理第1轴>65536，并满足Half/BFloat16的第0轴≤16，或Float的第0轴≤8；该选择看物理shape，没有另要求传入dim必须为1。

主线另以“**SoC枚举≥Ascend950且is_gte_cann_version_920()为真**”与旧gate取OR。所读helper静态缓存对`"8.3.RC1"`/`"9.2.0"`的CANN版本比较结果，不能把两个条件合并成所有SoC都只要新CANN。

主线进入任一SDK分支后，对负dim调用maybe_wrap_dim，检查非标量、split_sizes非负且求和等于选中轴长度、out个数一致；逐个必要时resize输出，**再**检查该输出dtype/device，最后调用aclnnSplitWithSize。前面已resize的输出不会因后面检查失败自动回滚。发布只有旧gate，通过后直接SDK，没有这些本地检查/resize或新增OR条件；其他情况两版均委托native实现。

这段Split包装没有显式缺符号探测或DO_COMPATIBILITY，不承诺SDK缺失时自动转native；即使形状满足优化门，也仍需实际环境中的内核可用。

## 固定证据

依据OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`和发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的完整三组包装与最小helpers/Schema。没有运行拼接、复制或设备实验；native/SDK内部、跨产品全部支持和实际加速比未由本卡证明。布局支持页见[Tensor布局](../../inference/guides/optimization/torch_npu/torch_npu_native_tensor_layout.md)。

## Evidence

- [CatKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/CatKernelNpuOpApi.cpp)（primary）：1–163；完整本地小文件。
- [ChunkCatKernelOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ChunkCatKernelOpApi.cpp)（primary）：1–130；完整本地小文件。
- [SplitWithSizesCopyNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SplitWithSizesCopyNpuOpApi.cpp)（primary）：1–124；完整本地小文件。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：1561–1577、1786–1790、5570–5571；仅所选完整Schema条目。
- [OpUtils.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）：77–86、474–478、510–513；仅make_warp_dim与两个CANN版本helper。
- [op_api_common.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation）：767–773；仅双符号探测helper。
- [CatKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/CatKernelNpuOpApi.cpp)（implementation）：1–165；完整本地小文件。
- [ChunkCatKernelOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ChunkCatKernelOpApi.cpp)（implementation）：1–129；完整本地小文件。
- [SplitWithSizesCopyNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SplitWithSizesCopyNpuOpApi.cpp)（implementation）：1–66；完整本地小文件。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：1502–1518、1727–1731、5398–5399；仅所选完整Schema条目。
- [OpUtils.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）：75–84、430–434；仅make_warp_dim与CANN版本helper。
- [op_api_common.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp)（implementation）：785–792；仅双符号探测helper。
