---
type: Guide
title: 索引读取族执行：gather/index/index_select/index_fill 的派发与宿主读取
description: 核对 gather 输出取 index 形状、反向 zeros+scatter_add 组合与主线与发布两版本 的 sparse_grad 差异，以及 index.Tensor 占位空张量、index_select 定形和 index_fill 在 950 的逐元素宿主读取路由。并含 count_nonzero 的 ne+sum 组合、_unsafe_index.Tensor 的 v2.1 原生委托与 select/index_fill dimname 负向定案。并含 _npu_index_add/_npu_index_add_ 的注册面、生成体与跨仓所有权。
tags:
- task.optimization
- topic.memory
- topic.data_movement
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GatherKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GatherKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GatherBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GatherBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GatherSparseBackwardNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GatherSparseBackwardNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/IndexKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/IndexKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/IndexSelectKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/IndexSelectKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/IndexFillKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/IndexFillKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/CountNonZeroKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CountNonZeroKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UnsafeIndexKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/CountNonZeroKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/CountNonZeroKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UnsafeIndexKernelNpuOpApi.cpp
  role: implementation

created_at: '2026-11-12T13:29:48Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 索引读取族执行：gather/index/index_select/index_fill 的派发与宿主读取

## 固定准确入口

本卡覆盖索引/读取家族中此前仅有支持表行或家族级 receipt 的四组入口：gather（含 dimname 与反向）、`index.Tensor`（高阶索引读取）、index_select、index_fill/index_fill_（int_Scalar/int_Tensor × functional/inplace 四重载）。OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布 `dedc316708372c9a8bfde4527abd2a94b74840f5`；DO_COMPATIBILITY 双符号探测与 EXEC_NPU_CMD 语义复用 [索引写入卡](torch_npu_index_put_masked_fill_preparation_and_shortcuts.md)已核对的两仓固定来源，不在此重复。yaml 对这四组均登记 acl_op+op_api all_version 且**无 gen_opapi 段**——opapi 侧全部为手写包装（本卡即读这些包装）。只读静态审阅，未执行上游、设备或性能实验；950 文档层对 gather/index_select/scatter 重复索引的精度提示按 [torch 支持范围卡](torch_npu_native_torch_index_reduce_scope.md)原口径消费，本卡不重复。

## gather：输出取 index 形状，反向是 zeros+scatter_add 组合

前向（主线与发布两版本 语义相同）：DO_COMPATIBILITY(aclnnGather) 后，functional 以 `apply_tensor_without_format(self, index.sizes())` 申请——**dtype 取 self、形状取 index，不做任何广播**；out 重载 `check_tensor({self}, out, self.scalar_type(), index.sizes())`；随后单次 EXEC aclnnGather(self, dim, index, result)。Schema 的 `sparse_grad` 参数不转发给命令，只被反向消费。

dimname 过载：yaml 主线与发布两版本 均登记 gather.dimname/dimname_out；主线 opapi 以 `#if !VERSION_BETWEEN(V2R13, VERSION_NEWEST)` 把 dimname 包装**编译期排除在 V2R13+ 之外**（内部经 dimname_to_position 转整数维后走同一路径）；发布 opapi 文件不含任何 dimname 函数。注册面与实现面在 V2R13 命名维上出现缝隙：登记仍在而包装不可用，V2R13 上 dimname 调用最终落到哪条分派未在源内核对。

反向（derivatives.yaml 12–17，主线与发布两版本 相同）：self → `npu_gather_backward(grad, self.sym_sizes(), dim, index, sparse_grad)`；index: non_differentiable；result: auto_linear。`npu_gather_backward` 在 yaml custom 与 symint 两段登记、均仅 op_api。主线实现（GatherBackwardKernelNpuOpApi.cpp）：

- `sparse_grad=True`：在 host 构造 COO 稀疏返回值。0 维 self 用 `empty({0, grad.numel()}, index.options())`、0 维 grad 用 `index.view({1,1})` 两个特例；一般情形分配 `{self_dim, grad.numel()}` 的 Long 坐标并逐维生成——dim 维取 `index.reshape(-1)`，其余维 `arange(size).unsqueeze(1).expand({size, n_above}).reshape(-1).repeat(n_below)`——最后 `_sparse_coo_tensor_unsafe(sparse_ind, grad.reshape(-1), self_size)`。
- `sparse_grad=False`：`grad.new_zeros_symint(self_size)` 后 `scatter_add_(dim, index, grad)`；index/grad 任一为 Tensor 子类时改用非原地 `scatter_add`（源码注释标明为 composite/vmap/inductor 合规）。
- **发布版本 对 sparse_grad=True 直接 TORCH_CHECK 抛错**（"npu_gather_backward not support sparse"），没有稀疏构造分支——同名自定义反向在主线与发布两版本 行为不同，迁移组合时须分别核对。

相邻入口 `npu_gather_sparse_index_backward`（GatherSparseBackwardNpuOpApi.cpp，主线与发布两版本 去空白 token 流相同）：`grad.new_zeros_symint(self_sizes)` 后调用 custom `_npu_index_add(_)`（Tensor 子类走非原地变体）。`_npu_index_add` 的实现符号位于 torch_npu 仓（aten inventory (b) 排除项），本卡只核对 op-plugin 侧消费者，不展开其内核。

性能口径：gather 反向不是单一 device 命令，而是 zeros + scatter_add 的组合；主线 sparse_grad=True 还会构造整组 Long 坐标 Tensor。这些是 host 可见的组合形态，不等于实测 kernel 数或耗时。

## index.Tensor：占位空张量与单命令 aclnnIndex

DO_COMPATIBILITY(aclnnIndex) 缺符号时回退 `acl_op::index`。直发路径先复用 [索引写入卡](torch_npu_index_put_masked_fill_preparation_and_shortcuts.md)已核对的 AdvanceIndex 工具：`checkIndexTensorTypes(orig)` 判定 needCast，`npu_expand_tensors(self, orig, needCast, true)` 做索引展开与设备迁移。

之后走**另一条准备链**：所有 undefined 索引槽统一替换为一个 `apply_tensor_without_format(self, {0})` 的空占位张量（单次申请、逐槽复用）；输出由 `index_npu_output_size(self, indices)` 定形后 `apply_tensor_without_format(self, output_size)` 申请；indices 以 TensorList 一次性 EXEC aclnnIndex。与 index_put 的 make_info/hasContiguousSubspace/transposeToFront 被索引维度重排不同，本入口不重排维度、不构造 replacement shape。aclnnIndex 对占位空张量与混合 dtype 索引的实际接受范围在设备侧未核对；`acl_op::index` 回退的完整组合行为也未展开。

## index_select：helper 定形与单命令

out size 由 `index_select_npu_output_size(self, dim, index)` 计算；functional `apply_tensor_without_format(self, output_size)`；out `check_tensor({self, index}, result, self.scalar_type(), output_size)`；单次 EXEC aclnnIndexSelect。dimname 过载与 gather 同型：主线 V2R13 编译期排除、发布无 dimname 函数（可用区间内经 dimname_to_position 委托整数维实现）。

## index_fill/index_fill_：950 与符号探测切换的宿主索引读取

四个重载共享结构：Tensor value 先 TORCH_CHECK `value.dim()==0`，另有复数守卫（非复数 self + 复数 value 抛错）；每个入口以 `static const bool check_aclnn_kernel_available("aclnnIndexFill"/"aclnnInplaceIndexFill")` 做进程级一次探测缓存。

- **Tensor-array 路由**（`!available` 或 SoC≥Ascend950 时）：TORCH_CHECK `index.dim() <= 1`（"Index has to be a vector/scalar."）；`value.item()` 把 0 维值读成宿主 Scalar；`get_index_vector` 以**逐元素 `index[i].item().to<int>()`** 把索引读成宿主数组，再以 IntArrayRef 传 aclnnIndexFillTensor/aclnnInplaceIndexFillTensor。每个索引元素一次 `.item()` 宿主同步读——索引规模大时这是首要定位点，且该路由强制索引为一维以内。
- **Tensor 路由**（符号可用且非 950）：index 张量原样传 aclnnIndexFill/aclnnInplaceIndexFill，无宿主索引读取（value 仍经 `value.item()`）。
- functional 结果 `apply_tensor_without_format(self)` 申请并 propagate_names；两个路由的输出形状都与 self 相同。

pin 差异：主线 inplace 两变体的 950 门为 `SoC≥Ascend950 && !is_gte_cann_version_910()`——CANN≥9.10 的 950 回到 Tensor 命令路由；发布 inplace 与 functional 一样，只要 950+ 即切 Tensor-array 路由（functional 变体主线与发布两版本 均为 950+ 即切）。950DT deterministic 清单另列 index_copy/index_copy_（见 [deterministic 算法卡](torch_npu_deterministic_algorithm_scope.md)），index_copy 的实现未在本卡核对。

## 验收

按目标 SoC/CANN 组合分别核对：index_fill 实际落入哪条路由（950 是否逐元素宿主读取、主线 CANN≥9.10 是否回 Tensor 命令）；gather 反向的组合命令数与 sparse_grad=True 在主线与发布两版本 的可用性；index.Tensor 占位张量路径与 index_put 路径的分配差异。以命令名推断 device kernel 数、以注册名推断 dimname 可用性，都不作为验收依据。

## Evidence

- [GatherKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GatherKernelNpuOpApi.cpp)（primary）：1–90；完整本地小文件。
- [GatherKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GatherKernelNpuOpApi.cpp)（implementation）：1–66；完整本地小文件，无 dimname 函数，其余仅排版差异。
- [GatherBackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GatherBackwardKernelNpuOpApi.cpp)（implementation）：20–82；npu_gather_backward_symint 完整函数体（sparse COO 构造 + zeros/scatter_add）。
- [GatherBackwardKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GatherBackwardKernelNpuOpApi.cpp)（implementation）：20–39；发布版完整函数体：TORCH_CHECK(!sparse_grad) + zeros/scatter_add。
- [GatherSparseBackwardNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GatherSparseBackwardNpuOpApi.cpp)（implementation）：17–30；npu_gather_sparse_index_backward_symint 完整函数体。
- [GatherSparseBackwardNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GatherSparseBackwardNpuOpApi.cpp)（implementation）：17–30；与主线去空白 token 流相同。
- [IndexKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/IndexKernelNpuOpApi.cpp)（implementation）：1–51；完整本地小文件。
- [IndexKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/IndexKernelNpuOpApi.cpp)（implementation）：1–51；与主线去空白 token 流相同。
- [IndexSelectKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/IndexSelectKernelNpuOpApi.cpp)（implementation）：1–51；完整本地小文件。
- [IndexSelectKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/IndexSelectKernelNpuOpApi.cpp)（implementation）：1–47；仅排版差异。
- [IndexFillKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/IndexFillKernelNpuOpApi.cpp)（implementation）：1–138；完整本地小文件（四个重载全部）。
- [IndexFillKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/IndexFillKernelNpuOpApi.cpp)（implementation）：1–122；完整本地小文件，inplace 950 门缺 is_gte_cann_version_910 条件。
- [derivatives.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）：12–17；仅 gather 反向公式条目。
- [derivatives.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）：12–17；同条目，与主线文字相同。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：2397–2412、2701–2704、2740–2755、2764–2779、5675–5676、7230–7245、7603–7604；仅本卡四组入口与 npu_gather* 自定义条目。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：2322–2337、2615–2618、2654–2669、2678–2692、5436–5437、7033–7034、7359–7360、7362–7363；同组条目（发布无 to_padded_tensor 等无关差异不在本卡范围）。

## count_nonzero 组合、_unsafe_index 原生委托与 g15 剩余负向

本节核对 g15 读取族剩余登记名：count_nonzero/count_nonzero.dim_IntList 与 _unsafe_index.Tensor，并按账本逐名定案 select 与 index_fill dimname 变体。yaml 登记：count_nonzero 两名主线与发布两版本 均`acl_op: all_version`+`op_api: all_version`且无 gen_opapi 段（主线 1885–1891、发布 1826–1832）；_unsafe_index.Tensor 主线与发布两版本 均仅`op_api: v2.1`+`internal_format_opapi: v2.1`、无 acl_op 行（主线 772–774、发布 747–749）。opapi/aclops 的 CountNonZero 两个文件主线与发布两版本 去空白字符流相同（尾注释排版差异），UnsafeIndex 同（主线 30 行、发布 31 行）。

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| `count_nonzero` opapi（主线 22–31）与 aclops（主线 23–32）双重载：`count_nonzero(self, dim: int?)` 有值时包成`IntArrayRef{dim.value()}`、无值时传空列表委托 IntArrayRef 重载；IntArrayRef 重载体是**纯组合**：`sum((self != 0), dim, false, at::ScalarType::Long)` | opapi 文件重入`op_api::sum`、aclops 文件调`acl_op::sum`——两条命名空间路径各回本族 sum 的 DO_COMPATIBILITY 与实现（[归约准备卡](torch_npu_reduction_scan_dtype_empty_and_alias_preparation.md)范围，本节不重复）；`(self != 0)`走 ATen ne 分发（g19，Bool 中间张量），ne 的 NPU 路由不在本节展开；无 aclnnCountNonZero 命令、无 out 变体、无 DO_COMPATIBILITY——空 Tensor/空维报错面由 sum 与 ne 承担，本层无独立检查；Bool 输入能否被 sum 走通属归约卡范围，不在此断言 |
| `_unsafe_index.Tensor` opapi（主线 24–28）：`#if VERSION_BETWEEN(V2R1, V2R1)`编译保护内单函数：`return at::native::_unsafe_index(self, indices);` | **仅 PyTorch 2.1 版本编译**（VERSION_BETWEEN(V2R1, V2R1) 单点区间），与 yaml `op_api: v2.1` 一致；v2.1 以外的固定源码无此函数——`_unsafe_index` 的其余版本框架侧路由不在本源集；函数体是**纯 ATen 原生委托**：无 aclnn 命令、无 DO_COMPATIBILITY、无 host 检查——at::native::_unsafe_index 内部（pytorch 仓）未核对，indices 稀缺项处理、布局与索引组合语义不据"unsafe"名字断言；图模式另一口径：torchair converter 对 BOOL/UINT8 self 明确拒绝等已由 [图索引卡](../../inference/guides/optimization/torchair/torchair_ge_index_scatter_lowering.md)核对，图侧拒绝不反推 eager 委托路径有同样检查，也不互推 |
| 负向定案一：`select`（含 select.int/select.Dimname 等任意变体）主线与发布两版本 yaml 全文 rg 零命中 | op-plugin 侧无任何 select 注册、无 SelectKernelNpu 实现文件——eager 框架侧分发（ATen/torch_npu/组合视图）不在本源集，不据零登记断言不可用；图侧 select.int→GatherV2 的 [图索引卡](../../inference/guides/optimization/torchair/torchair_ge_index_scatter_lowering.md)口径是 torchair converter 层，与 eager 不互推 |
| 负向定案二：`index_fill.dimname`/`index_fill_.dimname` 主线与发布两版本 yaml 全文 rg 零命中 | index_fill 家族只登记 int_Scalar/int_Tensor × functional/inplace 四重载（上文已核对）；"index_fill dimname 变体"作为账本候选按零登记定案，不构成缺失能力或存在能力的声明 |
| 账本核对：`index_add.dimname` 已由 [索引累加卡](torch_npu_indexed_add_buffer_preparation.md)核对（主线 Dimname 重载置`!VERSION_BETWEEN(V2R13, VERSION_NEWEST)`编译条件、发布无保护，dimname_to_position 转位置后进整数 dim 入口） | 本卡不重复；g15 读取族登记名至此核对，账本三态修订属 inventory 独立任务 |

count_nonzero 迁移/定位时记录实际落入的 sum 路径（op_api 直发还是 acl_op 回退）与 ne 中间张量的 dtype；`_unsafe_index` 仅在 v2.1 组合核对注册与编译面。本节静态审阅，未运行上游或设备，无新增平台承诺。

### count_nonzero 与 _unsafe_index 补充证据

- [CountNonZeroKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/CountNonZeroKernelNpuOpApi.cpp)（primary）：1–33；完整本地小文件（两个重载）。
- [CountNonZeroKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CountNonZeroKernelNpu.cpp)（primary）：1–34；完整本地小文件（两个重载）。
- [UnsafeIndexKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UnsafeIndexKernelNpuOpApi.cpp)（primary）：1–30；完整本地小文件。
- [CountNonZeroKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/CountNonZeroKernelNpuOpApi.cpp)（implementation）：1–39；完整本地小文件，与主线去空白字符流相同（尾注释排版差异）。
- [CountNonZeroKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/CountNonZeroKernelNpu.cpp)（implementation）：1–40；与主线去空白字符流相同。
- [UnsafeIndexKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UnsafeIndexKernelNpuOpApi.cpp)（implementation）：1–31；与主线逻辑结构一致（排版+尾注释差异）。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：772–774、1885–1891；_unsafe_index.Tensor 与 count_nonzero 两名条目完整字段（该文件已列于 frontmatter 来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：747–749、1826–1832；同条目，与主线逐字相同。
- 负向证据：`func: select`、`index_fill.{0,40}dimname`、`dimname.{0,40}index_fill` 在主线与发布两版本 yaml 全文 rg 零命中；`internal_format_opapi` 标记全仓使用 86/76 处（主线/发布），其消费语义未核对、本节按登记原文记录。

## _npu_index_add/_npu_index_add_的注册面、生成体与跨仓所有权

本节核对前文遗留的custom `_npu_index_add(_)`归属问题（上文按aten inventory (b)口径记为"实现符号位于torch_npu 仓"；[公开npu_gather_sparse_index卡](../../inference/apis/torch_npu/npu_gather_sparse_index.md)同样声明未沿私有helper展开）。六个固定版本静态对照结论：`npu::_npu_index_add`/`npu::_npu_index_add_`的schema注册与生成体登记都在op-plugin；torch_npu主线与发布两版本对该名零直接引用，仅经torchnpugen合并custom段生成`custom_ops::_npu_index_add(_)`分派桥（机制见[dtype转换卡](../../inference/guides/optimization/torch_npu/torch_npu_dtype_cast_backend_allocation_and_aliases.md)"从custom_ops调用到后端候选"节）。

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| 注册面（主线7246–7263、发布7036–7053，逐字相同）：`_npu_index_add(Tensor self, Tensor index, Tensor source, *, Scalar alpha=1)`与原地变体均`op_api: all_version`+gen_opapi，**无acl_op登记**。functional规格：out size=self/dtype=self、new_params `dim=(int64_t)0`、`mode=(int64_t)0`、exec `aclnnIndexAddV2, self, dim, index, source, alpha, mode, out`；原地变体同new_params，exec末位输出为self | schema无dim参数——custom变体固定沿第0维累加（dim/mode常量0），与aten公开index_add（可指定dim，g15另有闭环）不是同一入口，不互推 |
| 生成体（按已核对生成器模板推导，见[旧极值卡](../apis/torch_npu/legacy_min_max_and_sort.md) amax/amin节）：无acl_op→不生成DO_COMPATIBILITY符号探测；functional按out规格（size/dtype=self）申请/校验后单次EXEC aclnnIndexAddV2；原地变体直接以self作输出 | aclnnIndexAddV2符号缺失时的行为由EXEC_NPU_CMD运行时路径决定，无登记的acl_op回退目标；未运行gencode认证；aclnnIndexAddV2内核语义未核对 |
| 消费者（六个固定版本静态）：唯一 C++ kernel 调用方是本卡前文的npu_gather_sparse_index_backward（GatherSparseBackwardNpuOpApi.cpp 17–30，主线与发布两版本去空白等值：new_zeros_symint后Tensor子类走非原地、否则原地）；torch_npu主线/发布对该名rg零直接引用，op-plugin `op_plugin/ops/` 手写包装层除 GatherSparseBackwardNpuOpApi.cpp 外零命中——主线版本 另有的 python meta 注册与测试层命中见负向证据行，均非实现调用方 | index/source的shape合同未在wrapper层检查（交aclnnIndexAddV2）；alpha非1的数值行为未核对 |

### _npu_index_add补充证据

- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：7246–7263；_npu_index_add/_npu_index_add_两条件完整字段（含gen_opapi规格；该文件已列于frontmatter来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：7036–7053；与主线逐字相同。
- 负向证据：`_npu_index_add`在torch_npu主线/发布主线与发布两版本全树（*.cpp/*.h/*.py）零命中；op-plugin `op_plugin/ops/` 手写包装层（opapi/aclops）除GatherSparseBackwardNpuOpApi.cpp外零命中；无dimname/names变体条目；derivatives.yaml主线与发布两版本均无该名条目。主线版本另有非调用方命中：`op_plugin/python/meta/_meta_registrations.py` 1772–1777（`_npu_index_add(_)` 的 fake tensor meta 注册，functional empty_like 直返、原地返回 self）、`test/core_tests/test_fake_tensor.py` 6102–6134（test_npu_index_add/_ 两个行为测试存在，均标注 @unittest.skip "Skip until CANN supports aclnnIndexAddV2; do not execute"）、`test/core_tests/torch_npu_OpApi_schema_all.json` 4934/4937（发布 4796/4799，schema 登记佐证）与 config yaml 条目本身；发布版本仅yaml/schema两处。

## _npu_index_add 归属订正（六个固定版本 复核）

上文「`_npu_index_add` 的实现符号位于 torch_npu 仓（aten inventory (b) 排除项）」经六个固定版本 复核应订正：torch_npu 主线与发布两版本 全树（含 torchnpugen/）`_npu_index_add` **零命中**；实现登记在 op-plugin 主线与发布两版本 的 `op_plugin/config/op_plugin_functions.yaml`（主线 :7246/:7257、发布 :7036/:7047），`_npu_index_add(Tensor self, Tensor index, Tensor source, *, Scalar alpha=1)` 与 in-place 变体均为 `op_api: all_version` 的 gen_opapi 生成路：固定 `dim=(int64_t)0`、`mode=(int64_t)0` 两个 new_params，`exec: aclnnIndexAddV2`（out 变体 out size/dtype=self，in-place 以 self 为 out）。即 npu_gather_sparse_index_backward 的累加落点是 op-plugin 生成的首轴 IndexAddV2 封装，本卡消费者结论（new_zeros + 首轴 index_add，Tensor 子类走非原地变体）不变；GatherSparseBackwardNpuOpApi.cpp 中的 `custom_ops::_npu_index_add` 符号来自构建期生成的 CustomFunctions 头（生成机制见[类型转换后端卡](../../inference/guides/optimization/torch_npu/torch_npu_dtype_cast_backend_allocation_and_aliases.md) 的生成接线节），不表示 torch_npu 仓内有实现体。schema 无 dim 形参，不支持其他轴的推广。
