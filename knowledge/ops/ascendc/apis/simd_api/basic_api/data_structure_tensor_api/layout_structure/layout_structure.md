---
type: API
title: Layout数据结构
description: TensorAPI Layout 数据结构集，包含 Layout、Shape、Stride、Coord 及 MakeLayout、GetShape 等相关接口。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/layout_structure.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Layout数据结构

TensorAPI 中描述张量排布的 Layout 数据结构集合。基础结构含 Layout、Shape、Stride、Coord 及层次化表述法；构造与查询接口含 MakeLayout、MakeFrameLayout、MakeShape、MakeStride、MakeCoord、GetShape、GetStride、Get、Select、Squeeze、Capacity、Size、Coshape、Cosize、Rank。用于解耦张量的逻辑形状与物理排布，属试验特性。

<!-- cannbot:related:start -->
## 相关

- [noTrans extract 与 NDExtLayoutPtn 方向不匹配](../../../../../runbooks/precision/notrans_extract_ndextlayoutptn.md)（`exemplifies`）：noTrans extract 与 NDExtLayoutPtn 方向不匹配说明aclblasStrsm blocked 路径 noTrans misaligned 尝试 extract A/B 到对齐 workspace 再走 GEMM(transA=0)，extract 行主序存储与 blocked GEMM 的 NDExtLayoutPtn 读取方向不一致致精度大错（outliers 占比 48%~69%）；trans path 靠 transA=1 转置存储恰好匹配而工作；noTrans misaligned 一律回退 SIMT，extract+GEMM 路线 banned。
- [数据排布格式](../../../../../guides/technical_appendix/concepts_and_terms/neural_networks_and_operators/data_layout.md)（`explains`）：数据排布格式说明数据排布格式（Data Layout Format）是深度学习中对多维Tensor在内存中存储方式的描述。
- [Capacity（基础API）](capacity.md)（`related`）：Layout数据结构说明TensorAPI Layout 数据结构集，包含 Layout、Shape、Stride、Coord 及 MakeLayout、GetShape 等相关接口；对Capacity（基础API）而言，Capacity 是 Layout 可寻址元素容量，需用 Cosize/Size 的计算口径和 Layout 的 Shape/Stride 定义辨清含 padding 的内存范围。
- [GetStride](../../aux_data_structures/layout/get_stride.md)（`related`）：GetStride 与《Layout数据结构》的实质衔接是：GetStride 从 Layout 读取 MakeStride 生成的维度步长，Crd2Idx 以该 stride 映射坐标；NDDMA stride=0 故障和 Layout 说明验证物理寻址边界。
- [MakeShape](../../aux_data_structures/layout/make_shape.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《Layout数据结构》说明TensorAPI Layout 数据结构集，包含 Layout、Shape、Stride、Coord 及 MakeLayout、GetShape 等相关接口。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [Tensor数据结构](../tensor_structure/tensor_structure.md)（`related`）：Layout 提供 shape/stride 寻址，是 Tensor 的布局部分。
- [Coord（基础API）](coord.md)（`same_topic`）：焦点处理Coord 参与 Layout 坐标映射和 Tensor Slice 的用法；Layout数据结构正文说明“TensorAPI Layout 数据结构集，包含 Layout、Shape、Stride、Coord 及 MakeLayout、GetShape 等相关接口”。候选把 Coord 构造、Layout 映射、Crd2Idx 与 Slice 的正文调用关系展开。
- [ViewEngine](../tensor_structure/view_engine.md)（`same_topic`）：ViewEngine 与《Layout数据结构》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
<!-- cannbot:related:end -->
