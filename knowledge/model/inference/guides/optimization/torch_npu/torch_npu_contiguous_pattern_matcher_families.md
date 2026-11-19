---
type: Guide
title: TorchNPU 连续化 pattern 识别算法族：slice/select/broadcast/indexing/reshape 与组合推断
description: 逐 pattern 给出 can_use_* 识别门控、目标算子与 RECORD_FUNCTION 标记，区分真免拷贝（SetDesc/memRepoint）与换算子搬运，不把
  pattern 命中当作零拷贝。
tags:
- task.implementation
- topic.data_movement.layout_transform
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/slice_opt.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/select_opt.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/broadcast_opt.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/indexing_opt.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/combined_opt.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/reshapeV2_opt.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/reshape_opt.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/ReshapeOpt.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/ContiguousUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/contiguous/ContiguousUtils.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/contiguous/ReshapeOpt.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/contiguous/combined_opt.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/contiguous/indexing_opt.cpp
  role: implementation
created_at: '2026-11-13T04:24:55Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU 连续化 pattern 识别算法族：slice/select/broadcast/indexing/reshape 与组合推断

## 固定版本与范围

静态审阅 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 `torch_npu/csrc/framework/contiguous/` 下 slice/select/broadcast/indexing/combined/reshapeV2/reshape 各 pattern 文件与 `ContiguousUtils.cpp`。发布 pin `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 未在本卡逐行比对，跨版本使用前需按同文件核对。未确认产品范围，保持 `draft`、空平台；未导入上游、未运行设备或性能实验。调度入口、描述符缓存与克隆门控见[连续化描述符缓存与门控](torch_npu_contiguous_descriptor_cache_and_clone_gate.md)，组合开关的文档面见[编译缓存与组合连续化](torch_npu_aclop_cache_and_contiguous_views.md)。

## 候选 pattern 的选择顺序

`ContiguousTensorDesc::find_match_optimization_cases`（ContiguousUtils.cpp:29-54）按固定顺序归类：任一轴 stride 为 0 → 只登记 `broadcast`；存在相邻轴 stride 逆序（`strides_[i] < strides_[i+1]`）→ 只登记 `permute`；元素数少于 base（view 缩小）→ 同时登记 `slice`、`select`、`indexing` 三者。该归类是候选提示，不保证命中；命中与否仍由各 pattern 的 `can_use_*` 判定。

## slice：把 narrow 族 view 转成 npu_slice_out

`can_use_slice`（slice_opt.cpp:60-133）要求 view_strides 与 base_strides 完全一致、维度数不减、每轴只能不变或变小；storage_offset 按逐轴整除展开成 offsets，余数非 0 或 (offset+size) 越界即拒绝。最后一轴 stride 非 1 且基础格式且发生非末轴 narrow 时，按 `select(-1, k)` 语义补一个长度 1 的末轴再走 narrow 判定。命中后 `slice_to_contiguous` 用 base 尺寸重建视图并调用 `custom_ops::npu_slice_out`（:135-146），标记 `contiguous_d_Slice`/`cached_contiguous_d_Slice`。chunk/split/narrow 及部分 index 生成的 view 都落在这个 pattern 上；这是换算子搬运，不是零拷贝。

## select 与 indexing：StridedSlice 语义

`can_use_select`（select_opt.cpp:38-103）识别"去掉一维"的 select：base 与 view 维度差恰为 1，仅一轴 start/size 改变，offset 能被该轴 stride 整除。命中后构造 StridedSlice 参数调用 `custom_ops::npu_indexing_out`，长度 1 且原维宽非 1 的轴累计 `shrink_mask`（:105-125），标记 `contiguous_d_StridedSlice`。`can_use_indexing`（indexing_opt.cpp:31-96）识别带步长的索引 view：元素数必须少于 base、每轴 view_stride 是 base_stride 的不小于 1 的整数倍且 base_stride 非 0，由 offset/stride 反推 start、step、end；同样落到 `npu_indexing_out`。两 pattern 共享目标算子，但识别门控互不相同，不能因算子同名合并判断。

## broadcast：expand 维的重建

`can_use_broadcast`（broadcast_opt.cpp:36-66）仅处理"前插维度"的 expand：新增维 append 在前，其余轴要么 stride 非 0 且 size/stride 与 base 完全一致，要么 stride 为 0 且 base size 为 1、view size 任意；至少要有一个 stride-0 轴。命中后把 stride-0 轴尺寸置 1 重建临时视图，确认连续后调用 `custom_ops::npu_broadcast_out`（:68-89），标记 `contiguous_d_BroadcastTo`。temp_src 不连续时直接失败，不回退其他 pattern。

## reshape 与 reshapeV2：真免拷贝的两条路

`ReshapeContiguousOpt`（reshape_opt.cpp:12-28）在 `check_reshape_match` 通过后调用 `custom_ops::npu_reshape_out`，标记 `contiguous_d_Reshape`。`check_reshape_match`（ReshapeOpt.cpp:55-77）要求源与目标都连续、sizes 全等；非基础格式还需过 `can_use_memcpy_for_other_format`：NZ 要求最后两维 16 对齐且与 base 一致（且不允许"未对齐+偏移非 0"同时成立），其他格式要求 base_sizes==sizes 且 numels 与 storage_sizes 一致（无 padding）。`reshapeV2`（reshapeV2_opt.cpp:17-98）是主线新增的第二路线：`reshape_match_by_memory_repoint` 对 Half/BFloat16/Float/Byte/Char/Short/Int/Long/Float8_e5m2/Float8_e4m3fn 直接把目标存储 data_ptr 重指到 `base+offset`（`ResetDataPtr`，标记 `contiguous_h_memRepoint`），其他 dtype 回退 d2dCopyAsync；`can_use_memory_repoint` 要求基础格式，或 NZ 且最后两维 16 对齐（无 padding）。memRepoint 是地址重指的真免拷贝路径，但仅限列出的 dtype，且不改变源存储的格式描述。

## combined：组合 view 的推断与无拷贝刷新

`CombinedContiguousOpt::Optimizer`（combined_opt.cpp:17-37）在 `COMBINED_ENABLE` 开启时最多尝试两个组合 view（`MaxCombinedCasesNum` 默认 2，注释声明 n>2 也可支持），命中后先按 base_sizes 重建 base_tensor 再 `combined_to_contiguous`，并写描述符缓存。`cases_avoid`（:100-110）对含 stride-0（expand）的组合直接放弃。`reshape_without_copy_match`（:96-109）在 sizes 与 base_sizes 元素数一致且 storage_offset 等于 base_offset 时，仅调用 `StorageDescHelper::SetDesc` 刷新描述（标记 `contiguous_h_match`），是整族中唯一不动数据的分支。`can_infer_view_tensor`（:185-266 起）按 permute → select → slice 顺序做"反推 view 链"：maybe_permute 对 stride 逆序 view 排序 stride 并回填 size（重复 stride 的维记 1）；maybe_select/maybe_slice 是弱约束预筛（combined_opt.cpp:124-183）。`can_be_optimize_from_default_cases` 会用 {"reshape","slice","select"} 子集重试，且内部调用把 OpenCombined 显式置 false 防递归（:112-122）。

## 观测与优化判断

各 pattern 的 RECORD_FUNCTION 标记（`contiguous_d_Slice`、`contiguous_d_StridedSlice`、`contiguous_d_BroadcastTo`、`contiguous_d_Reshape`、`contiguous_h_memRepoint`、`contiguous_h_match`、`contiguous_h_combined` 及 cached_ 变体）可在 profiler 中确认实际分支。判断收益时应区分三类：地址重指/描述刷新（memRepoint、h_match）接近零成本；换算子搬运（slice/indexing/broadcast/reshape_out）把通用拷贝换成带语义的算子，仍发生数据移动；未命中则回到通用 `npu_stride_copy_out`（标记 `contiguous_d_AsStrided`，见门控卡）。pattern 命中不等于数值或别名契约变化：`npu_slice_out` 等仍是拷贝语义。本卡未审阅缓存并发安全、算子内部实现与发布版差异。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/slice_opt.cpp)（primary）：17-149 全文。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/select_opt.cpp)（primary）：15-128 全文。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/broadcast_opt.cpp)（primary）：15-96 全文。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/indexing_opt.cpp)（primary）：15-132（识别与落地函数；`indexing_to_contiguous` 体未逐行）。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/combined_opt.cpp)（primary）：17-110、112-266（Optimizer/CachedOptimizer、cases_avoid、无拷贝刷新、maybe_* 与 can_infer_view_tensor 主体；266-471 的 combined_to_contiguous 细节未逐行）。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/reshapeV2_opt.cpp)（primary）：15-107 全文。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/reshape_opt.cpp)（primary）：1-28 全文。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/ReshapeOpt.cpp)（primary）：15-89（1-14 为 include 头部未逐行）。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/ContiguousUtils.cpp)（implementation）：20-62（find_match_optimization_cases 与 reset/add case）。

## 发布 pin 对照（f3ecfe4a）

卡内涉及的 4 个发布孪生文件已做真实机械比对（sha256 → 去空白 → token → 注释剥离 token → 语义 diff 五级），结论分述如下。

### 已绑定（等价/无行为差异）

- `torch_npu/csrc/framework/contiguous/ContiguousUtils.h`：唯一实质 token 差异：acl_base.h 的 include 路径由系统路径改为 third_party 相对路径（构建布局差异）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/framework/contiguous/ReshapeOpt.cpp`：去空白等价（发布版仅多一个尾部空行）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/framework/contiguous/combined_opt.cpp`：唯一实质差异：发布版新增 `#include <ATen/NamedTensorUtils.h>`（新增 include，无既有代码改动）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/framework/contiguous/indexing_opt.cpp`：注释差异等价（代码 token 流相同）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。

（本节静态比对，未运行/未编译；结论按文件分列，未列出的文件未比对。）
