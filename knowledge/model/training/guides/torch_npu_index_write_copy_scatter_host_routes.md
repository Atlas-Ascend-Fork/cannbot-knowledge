---
type: Guide
title: 索引写入族执行：index_copy/take/put_/masked_scatter/scatter 的派发与宿主成本
description: 核对 index_copy 的逐元素宿主循环与 clone、take 的 Gather 命令复用、put_ 的 ScatterNd 组合与拷回、masked_scatter 的 Bool 转换，以及 scatter 双路径的 dtype 处理与 reduce 字符串重载无回退的事实。
tags:
- task.optimization
- topic.memory
- topic.data_movement
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScatterKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ScatterKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/PutKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/PutKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MaskedScatterKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MaskedScatterKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/IndexCopyKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/IndexCopyKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/TakeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/TakeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/PutKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/PutKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MaskedScatterKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MaskedScatterKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ScatterKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ScatterKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/IndexCopyKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/IndexCopyKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-12T14:09:45Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# 索引写入族执行：index_copy/take/put_/masked_scatter/scatter 的派发与宿主成本

读取族（gather/index/index_select/index_fill）见 [索引读取族卡](torch_npu_gather_index_fill_host_read_routes.md)。本卡核对写入族的 11 名：index_copy/index_copy.out/index_copy_、take/take.out、put_、masked_scatter_、scatter.src_out/scatter.value_out/scatter_.src/scatter_.value。yaml 主线与发布两版本 同语义：index_copy 与 take 为 gen 直发（index_copy out size/dtype=self、exec aclnnIndexCopy；index_copy_ exec aclnnInplaceIndexCopy；take.out out **size=index、dtype=self**、exec aclnnTake，functional structured_inherit）；index_copy.out **仅 op_api（无 acl_op 行）**；put_/masked_scatter_/scatter 四变体无 gen_opapi——手写 opapi 文件承接。**负向确认（主线与发布两版本 yaml 均无条目）**：take_along_dim、put（functional）、masked_scatter（functional）、scatter.src/scatter.value（functional）、scatter.value_reduce 未在来源 op-plugin 登记，其框架侧分派不在本卡范围。

| 入口 | op_api 路径 | acl_op 回退 |
| --- | --- | --- |
| index_copy / index_copy.out | gen 直发 aclnnIndexCopy（out 规格 size/dtype=self）；index_copy.out 无 acl_op 行，aclnnIndexCopy 缺失时无可回退 | **先 host 逐元素循环**：`index_copy_npu_impl` 对每个 index 元素 `index[i].item<int64_t>()` 读回后 `at::native::select`+`NPUNativeFunctions::copy_` 逐项拷贝；functional **无条件 `self.clone()`** 再入循环（非匹配格式再 format_contiguous）；index_copy_ 走格式分支+format_fresh_view |
| index_copy_ | gen exec aclnnInplaceIndexCopy | 同上 impl（contiguous_self 为 self 的格式化副本） |
| take / take.out | gen 直发 aclnnTake（size=index、dtype=self） | **复用 "Gather" 命令**（attr `validate_indices=false`）：self 先 `reshape(-1)`+format_contiguous，index format_contiguous；take_out CheckOut({self,index},out,self,input_same_output_size(index))+格式分支；functional `apply_tensor(self,index.sizes())` |
| put_ | 手写：DO_COMPATIBILITY(aclnnInplacePut)+`check_memory({self,index,source},{self})`+单命令 EXEC aclnnInplacePut | TORCH_CHECK index.numel()==source.numel()；source 为空提前返回；**flatten 后走 "ScatterNdAdd"（accumulate）/"ScatterNdUpdate"（非 accumulate）命令**（attr use_locking=false，输出写入 selfFlatten）后 **`self.copy_(selfFlatten)` 全量拷回**——host 侧至少两次整张量复制 |
| masked_scatter_ | 手写：DO_COMPATIBILITY(aclnnInplaceMaskedScatter)+check_memory+单命令 EXEC aclnnInplaceMaskedScatter | **非 Bool mask 先 `_npu_dtype_cast(mask,kBool)`**；"MaskedScatter" 命令；原地 check_match/format 分支 |
| scatter.src_out / scatter.value_out | 手写：DO_COMPATIBILITY(aclnnScatter/aclnnScatterValue)+`check_tensor({self,src,index}/{self,index},out,self)`+reduction=0+EXEC | "ScatterElements" 命令（axis attr）；**Half self 先 cast Float 计算再转回（out 变体 result.copy_）**；src dtype 与 self 不同时 cast 到 self dtype；**Scalar value 变体把标量物化为设备张量**：`scalar_to_tensor(value).to(Float)`+host-to-device 拷贝+`npu_broadcast` 到 index.sizes（inplace 变体改用 `copy_scalar_to_device(src,self.scalar_type())`，dtype 基准不同） |
| scatter_.src / scatter_.value | 手写：`check_tensor({…},self,self)`+EXEC aclnnInplaceScatter/aclnnInplaceScatterValue | 同上 ScatterElements 组合；原地 check_match/format 分支 |

三条需要单独记录的边界：

1. **reduce 字符串重载没有 DO_COMPATIBILITY 回退**：手写文件中带 `c10::string_view reduce` 的两个 scatter_out 重载只做 TORCH_CHECK（reduce 仅 add/multiply，映射 1/2）后直接 EXEC aclnnScatter/aclnnScatterValue，**不携带 `acl_op::` 回退分支**；aclnn 符号缺失时由 EXEC_NPU_CMD 自身的符号 TORCH_CHECK 报错，而不是走 ScatterElements 组合。带 reduce 的 ATen 调用在 yaml 未单列条目（scatter.value_reduce 负向确认见上）。
2. **index_copy 的 acl_op 回退成本形态特殊**：每索引一次 `.item()` 设备读回 + 一次 select + 一次 copy_，且 functional 先整量 clone；`index_copy_npu_par_check` 的边界检查本身也含逐元素 `.item()` 上界循环（index ≤ size-1），**未见负值下界检查**——负索引是否被 at::native::select 拦截未核对。950DT deterministic 清单已列 index_copy/index_copy_（见 [deterministic 算法卡](torch_npu_deterministic_algorithm_scope.md)），与本节静态事实互补。
3. **take 与 gather 的关系**：acl_op take 复用 "Gather" 命令并显式 `validate_indices=false`，self 展平为一维；与读取族卡的 aclnnGather 路径（out size=index.sizes()）相比，这里 dtype 按 self、形状按 index，gen 与 aclops 一致。put_ 的 950DT deterministic 清单条目与本卡实现层互不替代。

主线与发布两版本 差异如实：IndexCopy 两个文件仅 include 差异（NamedTensorCompat.h vs ATen/NamedTensorUtils.h），Scatter/Put/MaskedScatter/Take 的 opapi/aclops 文件语义等价（PutKernelNpuOpApi.cpp 与 aclops PutKernelNpu.cpp、Eye 同型字节相同，其余仅排版差异）；yaml 11 名条目主线与发布两版本 同语义。设备侧 aclnnIndexCopy/aclnnTake/aclnnInplacePut/aclnnInplaceMaskedScatter/aclnnScatter(*/Inplace*) 的内核语义、check_tensor/check_memory 内部实现均未核对；scatter_add/scatter_reduce/scatter_update 族已由 [索引累加卡](torch_npu_indexed_add_buffer_preparation.md)与 [torch 索引归约卡](torch_npu_native_torch_index_reduce_scope.md)核对，本卡不重复。

## Evidence

- [ScatterKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScatterKernelNpuOpApi.cpp)（implementation）：1–106；完整本地小文件。
- [ScatterKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ScatterKernelNpuOpApi.cpp)（implementation）：1–96；仅注释/排版差异，token 流相同。

- [PutKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/PutKernelNpuOpApi.cpp)（implementation）：1–32；完整本地小文件。
- [PutKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/PutKernelNpuOpApi.cpp)（implementation）：1–32；与主线字节相同。

- [MaskedScatterKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MaskedScatterKernelNpuOpApi.cpp)（implementation）：1–30；完整本地小文件。
- [MaskedScatterKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MaskedScatterKernelNpuOpApi.cpp)（implementation）：1–32；仅排版差异。

- [IndexCopyKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/IndexCopyKernelNpu.cpp)（implementation）：1–83；完整本地小文件（逐元素循环）。
- [IndexCopyKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/IndexCopyKernelNpu.cpp)（implementation）：1–83；仅 include 差异，语义相同。

- [TakeKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/TakeKernelNpu.cpp)（implementation）：1–60；完整本地小文件（Gather 命令）。
- [TakeKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/TakeKernelNpu.cpp)（implementation）：1–67；仅排版差异。

- [PutKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/PutKernelNpu.cpp)（implementation）：1–52；完整本地小文件（ScatterNd 组合+拷回）。
- [PutKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/PutKernelNpu.cpp)（implementation）：1–52；与主线字节相同。

- [MaskedScatterKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MaskedScatterKernelNpu.cpp)（implementation）：1–52；完整本地小文件（Bool cast）。
- [MaskedScatterKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MaskedScatterKernelNpu.cpp)（implementation）：1–62；仅排版差异。

- [ScatterKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ScatterKernelNpu.cpp)（implementation）：1–154；完整本地小文件（Half→Float、标量物化）。
- [ScatterKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ScatterKernelNpu.cpp)（implementation）：1–151；仅排版差异。

- [IndexCopyKernelNpu.cpp（custom_functions） d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/IndexCopyKernelNpu.cpp)（implementation）：1–70；完整本地小文件（par_check 宿主检查）。
- [IndexCopyKernelNpu.cpp（custom_functions） dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/IndexCopyKernelNpu.cpp)（implementation）：1–70；仅 include 差异，语义相同。

- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：2717–2739、3368–3371、4044–4047、4493–4508、5032–5046；仅本卡 11 名 Schema 条目。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：2631–2653、3263–3266、3932–3935、4366–4381、4872–4886；同 11 名条目。
